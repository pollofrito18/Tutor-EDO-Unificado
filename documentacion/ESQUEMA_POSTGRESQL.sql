BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001

CREATE TABLE limites (
    clave VARCHAR(100) NOT NULL, 
    cuenta INTEGER NOT NULL, 
    vence FLOAT NOT NULL, 
    PRIMARY KEY (clave)
);

CREATE TABLE usuarios (
    id VARCHAR(36) NOT NULL, 
    usuario VARCHAR(32) NOT NULL, 
    nombre VARCHAR(80) NOT NULL, 
    clave_hash TEXT NOT NULL, 
    creado FLOAT NOT NULL, 
    preferencias JSON NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_usuarios_usuario ON usuarios (usuario);

CREATE TABLE intentos (
    id VARCHAR(36) NOT NULL, 
    usuario_id VARCHAR(36) NOT NULL, 
    ejercicio VARCHAR(50) NOT NULL, 
    respuesta VARCHAR(350) NOT NULL, 
    correcto BOOLEAN NOT NULL, 
    creado FLOAT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_intentos_usuario_id ON intentos (usuario_id);

CREATE TABLE notificaciones (
    id VARCHAR(36) NOT NULL, 
    usuario_id VARCHAR(36) NOT NULL, 
    texto VARCHAR(300) NOT NULL, 
    evento VARCHAR(20) NOT NULL, 
    leida BOOLEAN NOT NULL, 
    creado FLOAT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_notificaciones_usuario_id ON notificaciones (usuario_id);

CREATE TABLE progreso (
    id VARCHAR(36) NOT NULL, 
    usuario_id VARCHAR(36) NOT NULL, 
    leccion VARCHAR(50) NOT NULL, 
    completada BOOLEAN NOT NULL, 
    actualizado FLOAT NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT uq_progreso_usuario_leccion UNIQUE (usuario_id, leccion), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_progreso_usuario_id ON progreso (usuario_id);

CREATE TABLE resultados (
    id VARCHAR(36) NOT NULL, 
    usuario_id VARCHAR(36) NOT NULL, 
    tipo VARCHAR(20) NOT NULL, 
    titulo VARCHAR(160) NOT NULL, 
    creado FLOAT NOT NULL, 
    entrada JSON NOT NULL, 
    resultado JSON NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_resultados_creado ON resultados (creado);

CREATE INDEX ix_resultados_usuario_id ON resultados (usuario_id);

CREATE TABLE sesiones (
    token_hash VARCHAR(64) NOT NULL, 
    usuario_id VARCHAR(36) NOT NULL, 
    vence FLOAT NOT NULL, 
    PRIMARY KEY (token_hash), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_sesiones_vence ON sesiones (vence);

CREATE INDEX ix_sesiones_usuario_id ON sesiones (usuario_id);

CREATE TABLE conversaciones (
    id VARCHAR(36) NOT NULL, 
    usuario_id VARCHAR(36) NOT NULL, 
    titulo VARCHAR(100) NOT NULL, 
    resultado_id VARCHAR(36), 
    creado FLOAT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE, 
    FOREIGN KEY(resultado_id) REFERENCES resultados (id)
);

CREATE INDEX ix_conversaciones_usuario_id ON conversaciones (usuario_id);

CREATE TABLE mensajes (
    id VARCHAR(36) NOT NULL, 
    conversacion_id VARCHAR(36) NOT NULL, 
    rol VARCHAR(12) NOT NULL, 
    texto TEXT NOT NULL, 
    creado FLOAT NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(conversacion_id) REFERENCES conversaciones (id) ON DELETE CASCADE
);

CREATE INDEX ix_mensajes_conversacion_id ON mensajes (conversacion_id);

INSERT INTO alembic_version (version_num) VALUES ('0001') RETURNING alembic_version.version_num;

COMMIT;

