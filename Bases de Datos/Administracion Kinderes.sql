PRAGMA foreign_keys = ON;

-- Catálogos básicos
CREATE TABLE Estado_catalogo (
  Estado_id INTEGER PRIMARY KEY,
  Nombre TEXT NOT NULL
);

CREATE TABLE Municipios_catalogo (
  Municipio_id INTEGER PRIMARY KEY,
  Nombre TEXT NOT NULL
);

CREATE TABLE Tipos_sangre (
  tipo_sangre INTEGER PRIMARY KEY,
  Sangre TEXT NOT NULL
);

CREATE TABLE Catalogo_discapacidades (
  Discapacidad_id INTEGER PRIMARY KEY,
  Nombre TEXT NOT NULL,
  descripcion TEXT
);

-- Sueldos de profesores
CREATE TABLE Sueldo_Profesores (
  Suel_id INTEGER PRIMARY KEY,
  Suel_Fecha TEXT,            -- almacenar fechas como TEXT ISO YYYY-MM-DD
  Suel_Monto REAL
);

-- Catálogos de movimientos y motivos
CREATE TABLE Movimientos_catalogo (
  Movimiento_id INTEGER PRIMARY KEY,
  Nombre_movimiento TEXT NOT NULL,
  descripcion TEXT
);

CREATE TABLE Motivo_catalogo (
  Motivo_id INTEGER PRIMARY KEY,
  Nombre TEXT NOT NULL,
  descripcion TEXT
);

-- Profesores
CREATE TABLE Profesores (
  Prof_id INTEGER PRIMARY KEY,
  Prof_Nombre TEXT,
  Prof_Apellido_paterno TEXT,
  Prof_Apellido_materno TEXT,
  Prof_CURP TEXT,
  Prof_correo TEXT,
  Prof_tipo_sangre INTEGER,
  Prof_alergias TEXT,
  Prof_Sueldo_id INTEGER,
  FOREIGN KEY (Prof_tipo_sangre) REFERENCES Tipos_sangre(tipo_sangre),
  FOREIGN KEY (Prof_Sueldo_id) REFERENCES Sueldo_Profesores(Suel_id)
);

-- Direccion_general (sin FK hacia Kinder para evitar circularidad)
CREATE TABLE Direccion_general (
  Dir_id INTEGER PRIMARY KEY,
  Dir_Nombre TEXT,
  Dir_Direccion TEXT,
  Dir_Correo_electronico TEXT,
  Dir_Num_celular TEXT,
  Dir_Num_fijo TEXT,
  Dir_Cod_postal INTEGER,
  Dir_Estado INTEGER,
  Dir_Municipio INTEGER,
  Dir_Kind_id INTEGER,        -- campo informativo, no FK para evitar circularidad
  FOREIGN KEY (Dir_Estado) REFERENCES Estado_catalogo(Estado_id),
  FOREIGN KEY (Dir_Municipio) REFERENCES Municipios_catalogo(Municipio_id)
);

-- SEP
CREATE TABLE SEP (
  SEP_id INTEGER PRIMARY KEY,
  SEP_NUM_afiliacion INTEGER,
  SEP_Afliado INTEGER,
  SEP_fecha TEXT,
  SEP_Kind_id INTEGER
);

-- Kinder (apunta a Direccion_general y SEP y Profesores y catálogos de estado/municipio)
CREATE TABLE Kinder (
  Kind_id INTEGER PRIMARY KEY,
  Kind_Nombre_kinder TEXT,
  Kind_SEP_id INTEGER,
  Kind_Direccion_general_id INTEGER,
  Kind_E_mail TEXT,
  Kind_direccion TEXT,
  Kind_Estado_id INTEGER,
  Kind_municipio_id INTEGER,
  Kind_botiquines INTEGER,
  Kind_extintores INTEGER,
  Kind_cod_postal INTEGER,
  Kind_SEP_Afliado INTEGER,
  Kind_Prof_id INTEGER,
  FOREIGN KEY (Kind_SEP_id) REFERENCES SEP(SEP_id),
  FOREIGN KEY (Kind_Direccion_general_id) REFERENCES Direccion_general(Dir_id),
  FOREIGN KEY (Kind_Estado_id) REFERENCES Estado_catalogo(Estado_id),
  FOREIGN KEY (Kind_municipio_id) REFERENCES Municipios_catalogo(Municipio_id),
  FOREIGN KEY (Kind_Prof_id) REFERENCES Profesores(Prof_id)
);

-- Alumno
CREATE TABLE Alumno (
  Al_Id INTEGER PRIMARY KEY,
  Al_Nombre TEXT,
  Al_Apellido_paterno TEXT,
  Al_Apellido_materno TEXT,
  Al_Alergias TEXT,
  Al_CURP TEXT,
  Al_Discapacidades_id INTEGER,
  Al_tipo_sangre INTEGER,
  FOREIGN KEY (Al_Discapacidades_id) REFERENCES Catalogo_discapacidades(Discapacidad_id),
  FOREIGN KEY (Al_tipo_sangre) REFERENCES Tipos_sangre(tipo_sangre)
);

-- Padre / tutor
CREATE TABLE Padre (
  Pad_id INTEGER PRIMARY KEY,
  Pad_Nombre TEXT,
  Pad_Apellidos TEXT,
  Pad_CURP TEXT,
  Pad_alumno_id INTEGER,
  Pad_correo TEXT,
  Pad_num_cel TEXT,
  Pad_num_trabajo TEXT,
  FOREIGN KEY (Pad_alumno_id) REFERENCES Alumno(Al_Id)
);

-- Colegiatura / pagos
CREATE TABLE Colegiatura (
  Pay_Id_Colegiatura INTEGER PRIMARY KEY,
  Pay_alumno_id INTEGER,
  Pay_monto REAL,
  Pay_pagado INTEGER,         -- usar 0/1 para boolean
  Pay_fecha TEXT,
  FOREIGN KEY (Pay_alumno_id) REFERENCES Alumno(Al_Id)
);

-- Movimientos financieros / administrativos
CREATE TABLE movimientos (
  Mov_id INTEGER PRIMARY KEY,
  mov_alumno_id INTEGER,
  Mov_Colegiatura_id INTEGER,
  Mov_fecha TEXT,
  Mov_Tipo INTEGER,
  Mov_Motivo INTEGER,
  FOREIGN KEY (mov_alumno_id) REFERENCES Alumno(Al_Id),
  FOREIGN KEY (Mov_Colegiatura_id) REFERENCES Colegiatura(Pay_Id_Colegiatura),
  FOREIGN KEY (Mov_Tipo) REFERENCES Movimientos_catalogo(Movimiento_id),
  FOREIGN KEY (Mov_Motivo) REFERENCES Motivo_catalogo(Motivo_id)
);
