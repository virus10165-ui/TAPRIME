-- Ручная SQL-версия миграции 0001_initial, чтобы проверить DDL на реальном Postgres
-- (в этой песочнице нет доступа к PyPI, поэтому Alembic не установить — проверяем схему напрямую)

CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    parent_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    head_user_id INTEGER
);
CREATE INDEX ix_departments_company_id ON departments(company_id);

CREATE TYPE userrole AS ENUM ('superadmin', 'company_admin', 'org_head', 'dept_head', 'employee');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role userrole NOT NULL,
    phone_number VARCHAR(32),
    is_2fa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE UNIQUE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_company_id ON users(company_id);

ALTER TABLE departments
    ADD CONSTRAINT fk_departments_head_user_id
    FOREIGN KEY (head_user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Проверка мультитенантной изоляции и ролей на тестовых данных
INSERT INTO users (company_id, email, hashed_password, full_name, role)
VALUES (NULL, 'admin@taprime.local', 'x', 'Platform Superadmin', 'superadmin');

INSERT INTO companies (name) VALUES ('Тестовая компания 1') RETURNING id;
INSERT INTO companies (name) VALUES ('Тестовая компания 2') RETURNING id;

INSERT INTO departments (company_id, name) VALUES (1, 'Бухгалтерия') RETURNING id;
INSERT INTO users (company_id, department_id, email, hashed_password, full_name, role)
VALUES (1, 1, 'admin1@company1.local', 'x', 'Админ компании 1', 'company_admin');

UPDATE departments SET head_user_id = (SELECT id FROM users WHERE email='admin1@company1.local') WHERE id = 1;

-- проверка тенант-изоляции: у компании 2 не должно быть отделов компании 1
SELECT company_id, count(*) FROM departments GROUP BY company_id;
SELECT id, email, company_id, role FROM users ORDER BY id;
