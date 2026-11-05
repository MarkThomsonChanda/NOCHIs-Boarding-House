create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  role text not null default 'student' check (role in ('student','owner')),
  full_name text not null default '',
  nrc_number text,
  phone text,
  residential_address text,
  guardian_name text,
  guardian_phone text,
  profile_picture_url text,
  created_at timestamptz not null default now()
);

create table if not exists public.rooms (
  room_number int primary key check (room_number between 1 and 28),
  price_kwacha numeric(10,2) not null,
  capacity int not null check (capacity > 0),
  is_available boolean not null default true
);

create table if not exists public.room_applications (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.profiles(id) on delete cascade,
  requested_room int not null references public.rooms(room_number),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  owner_note text,
  created_at timestamptz not null default now(),
  reviewed_at timestamptz
);

create table if not exists public.room_allocations (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null unique references public.profiles(id) on delete cascade,
  room_number int not null references public.rooms(room_number),
  allocated_at timestamptz not null default now()
);

create table if not exists public.payments (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.profiles(id) on delete cascade,
  amount_kwacha numeric(10,2) not null check (amount_kwacha > 0),
  payment_date date not null default current_date,
  payment_method text,
  reference text,
  status text not null default 'recorded' check (status in ('recorded','pending','reversed')),
  notes text,
  recorded_by uuid references public.profiles(id),
  created_at timestamptz not null default now()
);

create table if not exists public.room_swap_requests (
  id uuid primary key default gen_random_uuid(),
  student_id uuid not null references public.profiles(id) on delete cascade,
  current_room int not null references public.rooms(room_number),
  requested_room int not null references public.rooms(room_number),
  reason text,
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  owner_note text,
  created_at timestamptz not null default now(),
  reviewed_at timestamptz,
  check (current_room <> requested_room)
);

-- Seed all 28 rooms. Safe to run again.
insert into public.rooms(room_number, price_kwacha, capacity) values
  (1,1200,3),(2,1200,3),(3,1200,3),(4,1200,3),(5,1200,3),(6,1200,3),
  (7,1200,3),(8,1200,3),(9,1200,3),(10,1200,3),(11,1200,3),(12,1200,3),
  (13,1200,3),(14,1200,3),(15,1200,3),(16,1200,3),
  (17,1500,2),(18,1500,2),(19,1500,2),(20,1500,2),(21,1500,2),(22,1500,2),(23,1500,2),(24,1500,2),
  (25,1000,2),(26,1000,2),(27,1000,2),(28,1800,2)
on conflict (room_number) do update set price_kwacha=excluded.price_kwacha, capacity=excluded.capacity;

-- Supabase Auth creates a profile row for new users.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles(id, full_name, role)
  values (new.id, coalesce(new.raw_user_meta_data->>'full_name',''), 'student')
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
for each row execute procedure public.handle_new_user();

-- Row Level Security for direct Supabase client access.
alter table public.profiles enable row level security;
alter table public.rooms enable row level security;
alter table public.room_applications enable row level security;
alter table public.room_allocations enable row level security;
alter table public.payments enable row level security;
alter table public.room_swap_requests enable row level security;

create policy "profiles read own or owner" on public.profiles for select to authenticated
using (id = auth.uid() or exists(select 1 from public.profiles p where p.id=auth.uid() and p.role='owner'));
create policy "students update own profile" on public.profiles for update to authenticated
using (id=auth.uid()) with check (id=auth.uid());
create policy "rooms readable" on public.rooms for select to authenticated using (true);
create policy "applications own or owner read" on public.room_applications for select to authenticated
using (student_id=auth.uid() or exists(select 1 from public.profiles p where p.id=auth.uid() and p.role='owner'));
create policy "students create own applications" on public.room_applications for insert to authenticated
with check (student_id=auth.uid());
create policy "allocations own or owner read" on public.room_allocations for select to authenticated
using (student_id=auth.uid() or exists(select 1 from public.profiles p where p.id=auth.uid() and p.role='owner'));
create policy "payments own or owner read" on public.payments for select to authenticated
using (student_id=auth.uid() or exists(select 1 from public.profiles p where p.id=auth.uid() and p.role='owner'));
create policy "swap own or owner read" on public.room_swap_requests for select to authenticated
using (student_id=auth.uid() or exists(select 1 from public.profiles p where p.id=auth.uid() and p.role='owner'));
create policy "students create own swap" on public.room_swap_requests for insert to authenticated
with check (student_id=auth.uid());

-- After registering the owner's account, run in SQL Editor:
-- update public.profiles set role='owner' where id=(select id from auth.users where email='OWNER_EMAIL_HERE');
