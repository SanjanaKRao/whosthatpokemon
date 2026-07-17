create table if not exists public.leaderboard_scores (
    id bigint generated always as identity primary key,
    name text not null,
    country text not null default '🌍',
    score integer not null check (score >= 0),
    streak integer not null check (streak >= 0),
    generation_icon_url text,
    created_at timestamptz not null default now()
);

grant select, insert, update on table public.leaderboard_scores to service_role;
grant usage, select on sequence public.leaderboard_scores_id_seq to service_role;
