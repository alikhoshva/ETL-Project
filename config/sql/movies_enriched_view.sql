CREATE OR REPLACE VIEW movies_enriched_view AS
SELECT
    m."movieId",
    m.title,
    m.genres AS original_genres,
    m."imdbId",
    m."tmdbId",
    t.budget,
    t.api_genres,
    t.production_companies
FROM movies m
LEFT JOIN tmdb_data t ON m."tmdbId" = t."tmdbId";
