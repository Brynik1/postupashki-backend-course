-- 27. Пик онлайна против пика предыдущего эфира того же стримера.
-- Только площадка 'VK Play Live'; prev_peak — пик предыдущего по started_at эфира того
-- же стримера, delta — их разность; первый эфир каждого стримера не выводится.
--
-- Колонки: streamer, followers, started_at, title, peak_viewers, prev_peak, delta
-- Порядок: followers по убыванию, внутри стримера started_at по возрастанию
-- Строк:   592

WITH stream_peaks AS (
    SELECT
        s.nickname streamer,
        s.followers,
        st.started_at,
        st.title,
        st.peak_viewers,
        (
            SELECT prev.peak_viewers
            FROM streams prev
            WHERE prev.streamer_id = st.streamer_id
              AND (
                  prev.started_at < st.started_at
                  OR (
                      prev.started_at = st.started_at
                      AND prev.stream_id < st.stream_id
                  )
              )
            ORDER BY prev.started_at DESC, prev.stream_id DESC
            LIMIT 1
        ) prev_peak
    FROM streamers s
    JOIN platforms pl USING (platform_id)
    JOIN streams st USING (streamer_id)
    WHERE pl.name = 'VK Play Live'
)
SELECT
    streamer,
    followers,
    started_at,
    title,
    peak_viewers,
    prev_peak,
    peak_viewers - prev_peak delta
FROM stream_peaks
WHERE prev_peak IS NOT NULL
ORDER BY followers DESC, started_at;

