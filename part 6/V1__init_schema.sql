-- ============================================================
-- Схема базы данных: Информационная система стоматологической клиники
-- ВКР: Проектный практикум — Задание 6
-- СУБД: PostgreSQL 16
-- ORM: Hibernate / Spring Data JPA (Kotlin)
-- Версионирование: Flyway (V1__init_schema.sql)
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 1: doctors (Врачи)
-- Справочник врачей клиники
-- ─────────────────────────────────────────────────────────────
CREATE TABLE doctors (
    id          BIGSERIAL    PRIMARY KEY,
    last_name   VARCHAR(100) NOT NULL,
    first_name  VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    specialty   VARCHAR(200),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE doctors IS 'Справочник врачей стоматологической клиники';
COMMENT ON COLUMN doctors.specialty IS 'Специализация: терапевт, хирург, ортодонт, ортопед и др.';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 2: users (Пользователи — JWT аутентификация)
-- Связывается с doctors для привязки роли врача
-- Роли: ADMIN, DOCTOR, RECEPTIONIST
-- ─────────────────────────────────────────────────────────────
CREATE TABLE users (
    id          BIGSERIAL    PRIMARY KEY,
    username    VARCHAR(100) NOT NULL,
    password    VARCHAR(255) NOT NULL,   -- BCrypt hash
    role        VARCHAR(50)  NOT NULL DEFAULT 'RECEPTIONIST',
    doctor_id   BIGINT       REFERENCES doctors(id) ON DELETE SET NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT chk_users_role CHECK (role IN ('ADMIN', 'DOCTOR', 'RECEPTIONIST'))
);

COMMENT ON TABLE users IS 'Пользователи системы для JWT-аутентификации';
COMMENT ON COLUMN users.password IS 'Хэш BCrypt. Никогда не хранится в открытом виде';
COMMENT ON COLUMN users.doctor_id IS 'NULL если пользователь не является врачом (регистратор, admin)';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 3: patients (Пациенты)
-- Карточка пациента клиники
-- ─────────────────────────────────────────────────────────────
CREATE TABLE patients (
    id          BIGSERIAL    PRIMARY KEY,
    last_name   VARCHAR(100) NOT NULL,
    first_name  VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    birth_date  DATE,
    phone       VARCHAR(20),
    created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE patients IS 'Карточки пациентов стоматологической клиники';
COMMENT ON COLUMN patients.birth_date IS 'Дата рождения для расчёта возраста';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 4: diagnoses (Диагнозы МКБ-10)
-- Справочник диагнозов по международной классификации болезней
-- Пример кодов: K02.1, K04.0, K05.1
-- ─────────────────────────────────────────────────────────────
CREATE TABLE diagnoses (
    id          BIGSERIAL    PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL,
    name        VARCHAR(300) NOT NULL,
    description TEXT,
    CONSTRAINT uq_diagnoses_code UNIQUE (code)
);

COMMENT ON TABLE diagnoses IS 'Справочник диагнозов по классификации МКБ-10 (раздел K00-K14)';
COMMENT ON COLUMN diagnoses.code IS 'Код МКБ-10, например: K02.1 (Кариес дентина)';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 5: treatment_materials (Лечебные материалы)
-- Справочник расходных материалов с текущей ценой
-- Цена хранится как snapshot в appointment_tooth_materials
-- ─────────────────────────────────────────────────────────────
CREATE TABLE treatment_materials (
    id         BIGSERIAL      PRIMARY KEY,
    name       VARCHAR(300)   NOT NULL,
    unit       VARCHAR(50),                -- мл, г, шт, упак
    price      DECIMAL(10,2)  NOT NULL,    -- текущая цена
    updated_at TIMESTAMP      NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE treatment_materials IS 'Справочник лечебных материалов с актуальной ценой';
COMMENT ON COLUMN treatment_materials.price IS 'Текущая цена. Историческая цена фиксируется в appointment_tooth_materials.price_at_time';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 6: appointments (Записи на приём)
-- Центральная операционная таблица системы
-- Статусы: SCHEDULED → CALLED → IN_PROGRESS → DONE / CANCELLED
-- ─────────────────────────────────────────────────────────────
CREATE TABLE appointments (
    id               BIGSERIAL      PRIMARY KEY,
    patient_id       BIGINT         NOT NULL REFERENCES patients(id),
    doctor_id        BIGINT         NOT NULL REFERENCES doctors(id),
    appointment_date DATE           NOT NULL,
    appointment_time TIME           NOT NULL,
    status           VARCHAR(50)    NOT NULL DEFAULT 'SCHEDULED',
    total_cost       DECIMAL(10,2)  NOT NULL DEFAULT 0,
    notes            TEXT,
    created_at       TIMESTAMP      NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_appointment_status
        CHECK (status IN ('SCHEDULED', 'CALLED', 'IN_PROGRESS', 'DONE', 'CANCELLED')),
    CONSTRAINT chk_total_cost_positive CHECK (total_cost >= 0)
);

COMMENT ON TABLE appointments IS 'Записи пациентов на приём к врачу';
COMMENT ON COLUMN appointments.status IS 'SCHEDULED: запланирован | CALLED: вызван | IN_PROGRESS: ведётся | DONE: завершён | CANCELLED: отменён';
COMMENT ON COLUMN appointments.total_cost IS 'Автоматически пересчитывается при изменении состава материалов';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 7: appointment_teeth (Зубы в приёме)
-- Зуб задаётся парой (quadrant: 1-4, tooth_number: 1-8)
-- Нотация ISO 3950: Q1-Q4, зубы 1-8
-- Уникальность: один зуб — один раз в одном приёме
-- ─────────────────────────────────────────────────────────────
CREATE TABLE appointment_teeth (
    id             BIGSERIAL  PRIMARY KEY,
    appointment_id BIGINT     NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
    quadrant       SMALLINT   NOT NULL,
    tooth_number   SMALLINT   NOT NULL,
    diagnosis_id   BIGINT     REFERENCES diagnoses(id) ON DELETE SET NULL,
    notes          TEXT,
    CONSTRAINT chk_quadrant      CHECK (quadrant BETWEEN 1 AND 4),
    CONSTRAINT chk_tooth_number  CHECK (tooth_number BETWEEN 1 AND 8),
    CONSTRAINT uq_appointment_tooth
        UNIQUE (appointment_id, quadrant, tooth_number)
);

COMMENT ON TABLE appointment_teeth IS 'Зубы, лечённые в рамках конкретного приёма';
COMMENT ON COLUMN appointment_teeth.quadrant IS 'Квадрант: 1=верхний-правый, 2=верхний-левый, 3=нижний-левый, 4=нижний-правый';
COMMENT ON COLUMN appointment_teeth.tooth_number IS 'Номер зуба в квадранте: 1=центральный резец, 8=зуб мудрости';

-- ─────────────────────────────────────────────────────────────
-- ТАБЛИЦА 8: appointment_tooth_materials (Материалы на зуб)
-- Связывает зуб с использованными материалами
-- price_at_time — snapshot цены на момент записи (история цен)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE appointment_tooth_materials (
    id                   BIGSERIAL      PRIMARY KEY,
    appointment_tooth_id BIGINT         NOT NULL REFERENCES appointment_teeth(id) ON DELETE CASCADE,
    material_id          BIGINT         NOT NULL REFERENCES treatment_materials(id),
    quantity             DECIMAL(8,3)   NOT NULL DEFAULT 1,
    price_at_time        DECIMAL(10,2)  NOT NULL,
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_price_at_time_positive CHECK (price_at_time >= 0)
);

COMMENT ON TABLE appointment_tooth_materials IS 'Материалы, использованные при лечении конкретного зуба';
COMMENT ON COLUMN appointment_tooth_materials.price_at_time IS 'Цена материала на момент записи приёма. Не изменяется при обновлении цены в справочнике';
COMMENT ON COLUMN appointment_tooth_materials.quantity IS 'Количество в единицах из treatment_materials.unit';

-- ─────────────────────────────────────────────────────────────
-- ИНДЕКСЫ — ускорение типовых запросов
-- ─────────────────────────────────────────────────────────────

-- Расписание на конкретную дату (DisplayBoard, фильтрация)
CREATE INDEX idx_appointments_date
    ON appointments (appointment_date);

-- Поиск всех приёмов пациента
CREATE INDEX idx_appointments_patient
    ON appointments (patient_id);

-- Поиск всех приёмов врача
CREATE INDEX idx_appointments_doctor
    ON appointments (doctor_id);

-- Зубы по приёму (cascade delete, частые JOIN)
CREATE INDEX idx_appointment_teeth_appt
    ON appointment_teeth (appointment_id);

-- Материалы по зубу (cascade delete, расчёт total_cost)
CREATE INDEX idx_tooth_materials_tooth
    ON appointment_tooth_materials (appointment_tooth_id);

-- Поиск пользователя по username (JWT login)
CREATE INDEX idx_users_username
    ON users (username);

-- ─────────────────────────────────────────────────────────────
-- НАЧАЛЬНЫЕ ДАННЫЕ (seed data)
-- ─────────────────────────────────────────────────────────────

-- Врачи
INSERT INTO doctors (last_name, first_name, middle_name, specialty) VALUES
    ('Иванов',  'Алексей',   'Петрович',   'Терапевт'),
    ('Петрова',  'Мария',     'Сергеевна',  'Хирург'),
    ('Сидоров',  'Кирилл',    'Вячеславович','Ортодонт'),
    ('Козлова',  'Наталья',   'Евгеньевна', 'Ортопед'),
    ('Морозов',  'Роман',     'Дмитриевич', 'Терапевт');

-- Пользователи (пароли: BCrypt от 'admin123' и 'doctor123')
INSERT INTO users (username, password, role, doctor_id) VALUES
    ('admin',    '$2a$12$exampleHashForAdmin...', 'ADMIN',        NULL),
    ('ivanov',   '$2a$12$exampleHashForDoc1...',  'DOCTOR',       1),
    ('petrova',  '$2a$12$exampleHashForDoc2...',  'DOCTOR',       2),
    ('register', '$2a$12$exampleHashForReg...',   'RECEPTIONIST', NULL);

-- Диагнозы МКБ-10 (раздел K — болезни органов пищеварения, подраздел K00-K14)
INSERT INTO diagnoses (code, name, description) VALUES
    ('K02.1', 'Кариес дентина',              'Поражение дентина кариозным процессом'),
    ('K02.2', 'Кариес цемента',              'Поражение цемента корня зуба'),
    ('K02.3', 'Приостановившийся кариес',    'Стабилизированный кариозный процесс'),
    ('K04.0', 'Пульпит',                     'Воспаление пульпы зуба'),
    ('K04.1', 'Некроз пульпы',               'Гангрена пульпы'),
    ('K04.4', 'Острый апикальный периодонтит','Острое воспаление периодонта'),
    ('K04.7', 'Периапикальный абсцесс',      'Гнойное воспаление в периапикальной области'),
    ('K05.1', 'Хронический гингивит',        'Хроническое воспаление дёсен'),
    ('K05.3', 'Хронический пародонтит',      'Хроническое воспаление пародонта'),
    ('K06.0', 'Рецессия десны',              'Обнажение корня зуба вследствие убыли десны'),
    ('K08.1', 'Потеря зуба вследствие несчастного случая', NULL),
    ('K08.2', 'Атрофия альвеолярного края',  'Резорбция альвеолярного отростка');

-- Лечебные материалы
INSERT INTO treatment_materials (name, unit, price) VALUES
    ('Пломбировочный материал Filtek Z250',    'г',   350.00),
    ('Анестетик Ультракаин DS 1.7мл',          'шт',  180.00),
    ('Антисептик Хлоргексидин 0.05%',          'мл',   45.00),
    ('Стеклоиономерный цемент Fuji II',        'г',   420.00),
    ('Металлокерамическая коронка',             'шт', 8500.00),
    ('Имплант Osstem US 3.5×10',               'шт', 25000.00),
    ('Брекет-система металлическая',            'комплект', 18000.00),
    ('Гуттаперча для пломбировки каналов',     'шт',   25.00),
    ('Штифт стекловолоконный',                  'шт',  650.00),
    ('Адгезивная система Optibond FL',          'мл',  280.00);
