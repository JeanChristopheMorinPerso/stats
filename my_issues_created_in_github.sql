-- Returns all issues that I created in GitHub.
SELECT
    concat('https://github.com/', repo_name, '/issues/', number) as url,
    title,
    created_at
FROM github_events
WHERE
    event_type = 'IssuesEvent'
    AND actor_login in ('JeanChristopheMorinPerso', 'JeanChristopheMorinRodeoFX')
    AND action = 'opened'
ORDER BY created_at;