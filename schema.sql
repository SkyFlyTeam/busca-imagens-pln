DROP TABLE IF EXISTS metadata_table;

CREATE TABLE metadata_table (
    id              SERIAL PRIMARY KEY,
    categoria       VARCHAR(30)  NOT NULL,
    data_imagem     DATE         NOT NULL,
    origem          VARCHAR(30)  NOT NULL,
    caminho_arquivo TEXT         NOT NULL,
    descricao       TEXT
);

CREATE INDEX idx_categoria ON metadata_table (categoria);
CREATE INDEX idx_origem    ON metadata_table (origem);
CREATE INDEX idx_data      ON metadata_table (data_imagem);
