import React, { useState } from 'react';
import { X, Star } from 'lucide-react';
import type { ReviewAspects } from '../hooks/useReviews';

interface ReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  bookingId: string;
  operator: string;
  route: string;
  userName: string;
  onSubmit: (
    bookingId: string,
    operator: string,
    route: string,
    overallRating: number,
    aspects: ReviewAspects,
    comment: string,
    userName: string,
  ) => void;
}

const ASPECTS: { key: keyof ReviewAspects; label: string; emoji: string }[] = [
  { key: 'cleanliness', label: 'Bus Cleanliness', emoji: '🚌' },
  { key: 'driverBehaviour', label: 'Driver Behaviour', emoji: '👨‍✈️' },
  { key: 'punctuality', label: 'Punctuality', emoji: '⏰' },
  { key: 'seatComfort', label: 'Seat Comfort', emoji: '💺' },
  { key: 'journeyExperience', label: 'Journey Experience', emoji: '🛣️' },
];

function StarRating({ value, onChange, size = 24 }: { value: number; onChange: (v: number) => void; size?: number }) {
  const [hover, setHover] = useState(0);

  return (
    <div className="star-rating" style={{ display: 'flex', gap: '4px' }}>
      {[1, 2, 3, 4, 5].map(star => (
        <button
          key={star}
          type="button"
          className={`star-btn ${star <= (hover || value) ? 'active' : ''}`}
          onMouseEnter={() => setHover(star)}
          onMouseLeave={() => setHover(0)}
          onClick={() => onChange(star)}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            transition: 'transform 0.15s ease',
            transform: star <= (hover || value) ? 'scale(1.15)' : 'scale(1)',
          }}
        >
          <Star
            size={size}
            fill={star <= (hover || value) ? '#f59e0b' : 'none'}
            color={star <= (hover || value) ? '#f59e0b' : 'rgba(255,255,255,0.2)'}
          />
        </button>
      ))}
    </div>
  );
}

export const ReviewModal: React.FC<ReviewModalProps> = ({
  isOpen,
  onClose,
  bookingId,
  operator,
  route,
  userName,
  onSubmit,
}) => {
  const [overallRating, setOverallRating] = useState(0);
  const [aspects, setAspects] = useState<ReviewAspects>({
    cleanliness: 0,
    driverBehaviour: 0,
    punctuality: 0,
    seatComfort: 0,
    journeyExperience: 0,
  });
  const [comment, setComment] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleAspectChange = (key: keyof ReviewAspects, value: number) => {
    setAspects(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = () => {
    if (overallRating === 0) return;
    onSubmit(bookingId, operator, route, overallRating, aspects, comment, userName);
    setSubmitted(true);
    setTimeout(() => {
      onClose();
      setSubmitted(false);
      setOverallRating(0);
      setAspects({ cleanliness: 0, driverBehaviour: 0, punctuality: 0, seatComfort: 0, journeyExperience: 0 });
      setComment('');
    }, 1500);
  };

  return (
    <div className="review-modal-overlay" onClick={onClose}>
      <div className="review-modal" onClick={e => e.stopPropagation()}>
        <button className="review-modal-close" onClick={onClose}>
          <X size={20} />
        </button>

        {submitted ? (
          <div className="review-success">
            <div className="review-success-icon">✅</div>
            <h3>Thank you for your review!</h3>
            <p>Your feedback helps other travelers.</p>
          </div>
        ) : (
          <>
            <div className="review-modal-header">
              <h3>⭐ Rate Your Journey</h3>
              <p className="review-route-info">
                {route} • {operator}
              </p>
            </div>

            <div className="review-section">
              <label className="review-label">Overall Rating</label>
              <StarRating value={overallRating} onChange={setOverallRating} size={32} />
            </div>

            <div className="review-section">
              <label className="review-label">Rate Specific Aspects</label>
              <div className="review-aspects">
                {ASPECTS.map(({ key, label, emoji }) => (
                  <div key={key} className="review-aspect-row">
                    <span className="aspect-label">{emoji} {label}</span>
                    <StarRating
                      value={aspects[key]}
                      onChange={v => handleAspectChange(key, v)}
                      size={18}
                    />
                  </div>
                ))}
              </div>
            </div>

            <div className="review-section">
              <label className="review-label">Write a review (optional)</label>
              <textarea
                className="review-textarea"
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="Share your experience..."
                rows={3}
                maxLength={500}
              />
            </div>

            <button
              className="review-submit-btn"
              onClick={handleSubmit}
              disabled={overallRating === 0}
            >
              ✅ Submit Review
            </button>
          </>
        )}
      </div>
    </div>
  );
};
