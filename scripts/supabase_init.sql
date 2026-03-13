-- 家庭菜谱同步：Supabase 初始化脚本
-- 在 Supabase SQL Editor 中执行

create table if not exists public.app_state (
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_app_state_updated_at on public.app_state;
create trigger trg_app_state_updated_at
before update on public.app_state
for each row
execute function public.set_updated_at();

insert into public.app_state (key, value)
values
  ('recipes', '{}'::jsonb),
  ('records', '[]'::jsonb),
  ('ingredients', '[]'::jsonb),
  ('accounts', '[]'::jsonb)
on conflict (key) do nothing;
