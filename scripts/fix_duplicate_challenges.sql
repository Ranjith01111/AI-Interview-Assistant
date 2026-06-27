-- Fix: Remove duplicate coding challenges (keep only first inserted per title)
-- Run: psql -U postgres -d interview_assistant -f scripts/fix_duplicate_challenges.sql

DELETE FROM coding_submissions
WHERE challenge_id IN (
    SELECT id FROM coding_challenges
    WHERE id NOT IN (
        SELECT DISTINCT ON (title) id
        FROM coding_challenges
        ORDER BY title, created_at ASC
    )
);

DELETE FROM coding_challenges
WHERE id NOT IN (
    SELECT DISTINCT ON (title) id
    FROM coding_challenges
    ORDER BY title, created_at ASC
);

-- Verify: should show 5 unique challenges
SELECT title, difficulty, id FROM coding_challenges ORDER BY title;
