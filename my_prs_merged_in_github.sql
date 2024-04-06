SELECT
    concat('https://github.com/', repo_name, '/pull/', toString(number)) AS URL,
    title, created_at, merged_at
FROM (
    SELECT *
    FROM (
        SELECT 
            repo_name, number, created_at, title
            FROM github_events
            WHERE
                event_type = 'PullRequestEvent'
                AND actor_login in ('JeanChristopheMorinPerso', 'JeanChristopheMorinRodeoFX')
                AND action = 'opened'
                AND repo_name != 'rodeofx/python-api'
                AND repo_name NOT LIKE 'AnacondaRecipes/%'
    ) AS t1
    INNER JOIN (
        SELECT
            repo_name, number, merged_at
            FROM github_events
            WHERE
                creator_user_login in ('JeanChristopheMorinPerso', 'JeanChristopheMorinRodeoFX')
                AND action = 'closed'
                AND merged_at != '1970-01-01 00:00:00'
                AND repo_name != 'rodeofx/python-api'
                AND repo_name NOT LIKE 'AnacondaRecipes/%'
    ) AS t2 USING (repo_name, number)
)
ORDER BY created_at
