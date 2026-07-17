create table if not exists public.pokemon_generation_icons (
    generation_key text primary key check (generation_key in ('gen1', 'gen2', 'gen3', 'gen4', 'gen5', 'gen6', 'gen7', 'gen8', 'gen9', 'all')),
    generation_label text not null,
    sort_order integer not null unique check (sort_order > 0),
    pokemon_id integer not null check (pokemon_id > 0),
    pokemon_name text not null,
    icon_url text not null,
    sprite_url text,
    created_at timestamptz not null default now()
);

grant select, insert, update on table public.pokemon_generation_icons to service_role;
