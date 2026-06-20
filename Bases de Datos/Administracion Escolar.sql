-- Elimina tablas en orden para evitar conflictos de FK (si existen)
DROP TABLE IF EXISTS Examenes;
DROP TABLE IF EXISTS Inscripciones;
DROP TABLE IF EXISTS Alumno;
DROP TABLE IF EXISTS catal_exam;
DROP TABLE IF EXISTS catal_estad_exam;
DROP TABLE IF EXISTS catal_materias;
DROP TABLE IF EXISTS catal_carreras;
DROP TABLE IF EXISTS Catal_turno;
DROP TABLE IF EXISTS Catal_Estado_materia;
DROP TABLE IF EXISTS Catal_Estado_carrera;
DROP TABLE IF EXISTS Catal_Estado_inscripcion;
DROP TABLE IF EXISTS Catal_estados;
DROP TABLE IF EXISTS Catal_Municipio;
DROP TABLE IF EXISTS Catal_Delegacion;


-- Tablas de catálogo
CREATE TABLE Catal_turno (
  cod_turno_769 INTEGER PRIMARY KEY,
  turno_769 VARCHAR,
  descripcion_769 VARCHAR
);

CREATE TABLE catal_carreras (
  clav_carrera_769 INTEGER PRIMARY KEY,
  carrera_nom_769 VARCHAR,
  semestres_769 INTEGER,
  plan_materias_769 INTEGER
);

CREATE TABLE catal_materias (
  cod_materias_769 INTEGER PRIMARY KEY,
  materia_769 VARCHAR,
  semestre_asignado_769 INTEGER
);

CREATE TABLE Catal_Estado_carrera (
  estado_carrera_769 INTEGER PRIMARY KEY,
  estado_769 VARCHAR,
  descripcion_769 VARCHAR
);

CREATE TABLE Catal_Estado_materia (
  estado_materia_769 INTEGER PRIMARY KEY,
  estado_769 VARCHAR,
  descripcion_769 VARCHAR
);

CREATE TABLE Catal_Estado_inscripcion (
  estado_carrera_769 INTEGER PRIMARY KEY,
  estado_769 VARCHAR,
  descripcion_769 VARCHAR
);

CREATE TABLE catal_estad_exam (
  cod_estado_769 INTEGER PRIMARY KEY,
  Estado_examen_769 VARCHAR,
  descripcion_769 VARCHAR
);

CREATE TABLE catal_exam (
  tipo_examen_769 INTEGER PRIMARY KEY,
  examen_769 VARCHAR,
  descripcion_769 VARCHAR
);

CREATE TABLE Catal_estados (
  Cod_estados INTEGER PRIMARY KEY,
  Estados VARCHAR
);

CREATE TABLE Catal_Municipio (
  Cod_Municipio_769 INTEGER PRIMARY KEY,
  Estados_769 INTEGER,
  Municipio_769 VARCHAR,
  CONSTRAINT fk_municipio_estado FOREIGN KEY (Estados_769) REFERENCES Catal_estados (Cod_estados)
);

CREATE TABLE Catal_Delegacion (
  Id_delegacion_769 INTEGER PRIMARY KEY,
  delegacion_769 VARCHAR
);

-- Tabla principal Alumno
CREATE TABLE Alumno (
  Cod_alumno_769 INTEGER PRIMARY KEY,
  apellidos_769 VARCHAR,
  nombres_769 VARCHAR,
  clav_carrera_769 INTEGER,
  estado_carrera_769 INTEGER,
  cod_materias_769 INTEGER,
  sexo_769 BOOLEAN,
  delegacion_769 INTEGER,
  municipio_769 INTEGER,
  estado_769 INTEGER,
  codigo_postal_769 INTEGER,
  cod_turno_769 INTEGER,
  CONSTRAINT fk_alumno_carrera FOREIGN KEY (clav_carrera_769) REFERENCES catal_carreras (clav_carrera_769),
  CONSTRAINT fk_alumno_estado_carrera FOREIGN KEY (estado_carrera_769) REFERENCES Catal_Estado_carrera (estado_carrera_769),
  CONSTRAINT fk_alumno_materia FOREIGN KEY (cod_materias_769) REFERENCES catal_materias (cod_materias_769),
  CONSTRAINT fk_alumno_turno FOREIGN KEY (cod_turno_769) REFERENCES Catal_turno (cod_turno_769),
  CONSTRAINT fk_alumno_delegacion FOREIGN KEY (delegacion_769) REFERENCES Catal_Delegacion (Id_delegacion_769),
  CONSTRAINT fk_alumno_municipio FOREIGN KEY (municipio_769) REFERENCES Catal_Municipio (Cod_Municipio_769),
  CONSTRAINT fk_alumno_estado FOREIGN KEY (estado_769) REFERENCES Catal_estados (Cod_estados)
);

-- Inscripciones
CREATE TABLE Inscripciones (
  clav_inscripcion_769 INTEGER PRIMARY KEY,
  cod_alumno_769 INTEGER,
  estado_materias_769 INTEGER,
  clav_carrera_769 INTEGER,
  fecha_769 TIMESTAMP,
  estado_carrera_769 INTEGER,
  cod_turno_769 INTEGER,
  CONSTRAINT fk_insc_alumno FOREIGN KEY (cod_alumno_769) REFERENCES Alumno (Cod_alumno_769),
  CONSTRAINT fk_insc_estado_materia FOREIGN KEY (estado_materias_769) REFERENCES Catal_Estado_materia (estado_materia_769),
  CONSTRAINT fk_insc_carrera FOREIGN KEY (clav_carrera_769) REFERENCES catal_carreras (clav_carrera_769),
  CONSTRAINT fk_insc_estado_carrera FOREIGN KEY (estado_carrera_769) REFERENCES Catal_Estado_inscripcion (estado_carrera_769),
  CONSTRAINT fk_insc_turno FOREIGN KEY (cod_turno_769) REFERENCES Catal_turno (cod_turno_769)
);

-- Examenes
CREATE TABLE Examenes (
  Cod_examenes_769 INTEGER PRIMARY KEY,
  tipo_examen_769 INTEGER,
  Cod_alumno_769 INTEGER,
  cod_carrera_769 INTEGER,
  cod_materia_769 INTEGER,
  fecha_apertura_769 TIMESTAMP,
  fecha_769 TIMESTAMP,
  cod_examen_769 INTEGER,
  Cod_turno_769 INTEGER,
  cod_estado_769 INTEGER,
  calificacion_769 INTEGER,
  CONSTRAINT fk_examen_alumno FOREIGN KEY (Cod_alumno_769) REFERENCES Alumno (Cod_alumno_769),
  CONSTRAINT fk_examen_tipo FOREIGN KEY (tipo_examen_769) REFERENCES catal_exam (tipo_examen_769),
  CONSTRAINT fk_examen_materia FOREIGN KEY (cod_materia_769) REFERENCES catal_materias (cod_materias_769),
  CONSTRAINT fk_examen_turno FOREIGN KEY (Cod_turno_769) REFERENCES Catal_turno (cod_turno_769),
  CONSTRAINT fk_examen_estado FOREIGN KEY (cod_estado_769) REFERENCES catal_estad_exam (cod_estado_769)
);

-- Índices sugeridos para búsquedas frecuentes
CREATE INDEX idx_alumno_carrera ON Alumno (clav_carrera_769);
CREATE INDEX idx_insc_alumno ON Inscripciones (cod_alumno_769);
CREATE INDEX idx_examen_alumno ON Examenes (Cod_alumno_769);
