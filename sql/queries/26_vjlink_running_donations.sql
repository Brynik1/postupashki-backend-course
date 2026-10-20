-- 26. Нарастающая сумма донатов внутри каждого стрима Вжлинка за 2021 год.
-- Стримы Вжлинка, начавшиеся в 2021 году по UTC, строка на каждый донат; running_total —
-- нарастающая сумма донатов своего стрима по sent_at_sec.
--
-- Колонки: stream_id, title, sent_at_sec, donor, amount, running_total
-- Порядок: stream_id по возрастанию, внутри стрима sent_at_sec по возрастанию
-- Строк:   192

SELECT
    st.stream_id,
    st.title,
    d.sent_at_sec,
    d.nickname donor,
    d.amount,
    (
        SELECT SUM(other.amount)
        FROM stream_donations other
        WHERE other.stream_id = d.stream_id
            AND (
                other.sent_at_sec < d.sent_at_sec
                OR (
                    other.sent_at_sec = d.sent_at_sec
                    AND other.donation_id <= d.donation_id
                )
            )
    ) running_total
FROM streamers s
JOIN streams st USING (streamer_id)
JOIN stream_donations d USING (stream_id)
WHERE s.nickname = 'Вжлинк'
  AND st.started_at >= TIMESTAMPTZ '2021-01-01 00:00:00+00'
  AND st.started_at < TIMESTAMPTZ '2022-01-01 00:00:00+00'
ORDER BY st.stream_id, d.sent_at_sec, d.donation_id;

