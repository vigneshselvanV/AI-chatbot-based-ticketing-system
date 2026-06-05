import { useState, useCallback, useEffect } from 'react';

export interface ReviewAspects {
  cleanliness: number;
  driverBehaviour: number;
  punctuality: number;
  seatComfort: number;
  journeyExperience: number;
}

export interface Review {
  id: string;
  bookingId: string;
  operator: string;
  route: string;
  overallRating: number;
  aspects: ReviewAspects;
  comment: string;
  userName: string;
  createdAt: string;
  verified: boolean;
}

export interface OperatorRating {
  operator: string;
  averageRating: number;
  totalReviews: number;
  topReviews: Review[];
}

const STORAGE_KEY = 'travel_ai_reviews';

function loadReviews(): Review[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Error loading reviews', e);
  }
  return [];
}

function saveReviews(reviews: Review[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
}

export function useReviews() {
  const [reviews, setReviews] = useState<Review[]>(loadReviews);

  useEffect(() => {
    saveReviews(reviews);
  }, [reviews]);

  const addReview = useCallback((
    bookingId: string,
    operator: string,
    route: string,
    overallRating: number,
    aspects: ReviewAspects,
    comment: string,
    userName: string,
  ): Review | null => {
    // Check if already reviewed
    const existing = reviews.find(r => r.bookingId === bookingId);
    if (existing) return null;

    const newReview: Review = {
      id: `REV-${Date.now()}`,
      bookingId,
      operator,
      route,
      overallRating,
      aspects,
      comment,
      userName,
      createdAt: new Date().toISOString(),
      verified: true,
    };

    setReviews(prev => [newReview, ...prev]);
    return newReview;
  }, [reviews]);

  const hasReviewed = useCallback((bookingId: string): boolean => {
    return reviews.some(r => r.bookingId === bookingId);
  }, [reviews]);

  const getReviewsForOperator = useCallback((operator: string): Review[] => {
    return reviews.filter(
      r => r.operator.toLowerCase() === operator.toLowerCase()
    );
  }, [reviews]);

  const getOperatorRating = useCallback((operator: string): OperatorRating => {
    const opReviews = getReviewsForOperator(operator);

    if (opReviews.length === 0) {
      return {
        operator,
        averageRating: 0,
        totalReviews: 0,
        topReviews: [],
      };
    }

    const avgRating = opReviews.reduce((sum, r) => sum + r.overallRating, 0) / opReviews.length;

    return {
      operator,
      averageRating: Math.round(avgRating * 10) / 10,
      totalReviews: opReviews.length,
      topReviews: opReviews.slice(0, 2),
    };
  }, [getReviewsForOperator]);

  const getAllOperatorRatings = useCallback((): Record<string, OperatorRating> => {
    const operators = new Set(reviews.map(r => r.operator));
    const ratings: Record<string, OperatorRating> = {};
    operators.forEach(op => {
      ratings[op.toLowerCase()] = getOperatorRating(op);
    });
    return ratings;
  }, [reviews, getOperatorRating]);

  const clearReviews = useCallback(() => {
    setReviews([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return {
    reviews,
    addReview,
    hasReviewed,
    getReviewsForOperator,
    getOperatorRating,
    getAllOperatorRatings,
    clearReviews,
  };
}
