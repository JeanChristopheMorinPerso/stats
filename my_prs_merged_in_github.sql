-- title: My PRs merged on GitHub
-- description: List of all PRs that I authored and eventually got merged on GitHub.
SELECT
    concat('https://github.com/', repo_name, '/pull/', toString(number)) AS URL,
    title AS Title, created_at AS "Created At", merged_at AS "Merged At"
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
