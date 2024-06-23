-- title: My issues created in GitHub
-- description: List of all issues that I created on GitHub.
SELECT
    concat('https://github.com/', repo_name, '/issues/', number) as URL,
    title AS Title,
    created_at AS "Created At"
FROM github_events
WHERE
    event_type = 'IssuesEvent'
    AND actor_login in ('JeanChristopheMorinPerso', 'JeanChristopheMorinRodeoFX')
    AND action = 'opened'
ORDER BY created_at;
