from pathlib import Path
import sqlite3

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent.parent
BANCO = BASE_DIR / "database" / "gastos.db"


def conectar_banco():
    conexao = sqlite3.connect(BANCO)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


@app.route("/")
def inicio():
    return "MicroDesafio Gastos funcionando!"


@app.route("/categorias", methods=["GET"])
def listar_categorias():
    try:
        with conectar_banco() as conexao:
            categorias = conexao.execute("""
                SELECT
                    id_categoria,
                    nome_categoria
                FROM categorias
                ORDER BY nome_categoria
            """).fetchall()

        resultado = [
            {
                "id_categoria": categoria["id_categoria"],
                "nome_categoria": categoria["nome_categoria"]
            }
            for categoria in categorias
        ]

        return jsonify(resultado), 200

    except sqlite3.Error as erro:
        return jsonify({
            "erro": "Não foi possível consultar as categorias.",
            "detalhes": str(erro)
        }), 500


@app.route("/gastos", methods=["GET"])
def listar_gastos():
    try:
        with conectar_banco() as conexao:
            gastos = conexao.execute("""
                SELECT
                    g.id_gasto,
                    g.descricao,
                    g.valor,
                    g.data_gasto,
                    g.forma_pagamento,
                    g.id_usuario,
                    g.id_categoria,
                    c.nome_categoria
                FROM gastos g
                LEFT JOIN categorias c
                    ON c.id_categoria = g.id_categoria
                ORDER BY g.id_gasto
            """).fetchall()

        resultado = [
            {
                "id_gasto": gasto["id_gasto"],
                "descricao": gasto["descricao"],
                "valor": gasto["valor"],
                "data_gasto": gasto["data_gasto"],
                "forma_pagamento": gasto["forma_pagamento"],
                "id_usuario": gasto["id_usuario"],
                "id_categoria": gasto["id_categoria"],
                "nome_categoria": gasto["nome_categoria"]
            }
            for gasto in gastos
        ]

        return jsonify(resultado), 200

    except sqlite3.Error as erro:
        return jsonify({
            "erro": "Não foi possível consultar os gastos.",
            "detalhes": str(erro)
        }), 500


@app.route("/gastos", methods=["POST"])
def cadastrar_gasto():
    dados = request.get_json(silent=True)

    if not dados:
        return jsonify({
            "erro": "Envie os dados do gasto em formato JSON."
        }), 400

    descricao = str(dados.get("descricao", "")).strip()
    valor = dados.get("valor")
    data_gasto = str(dados.get("data_gasto", "")).strip()
    forma_pagamento = str(
        dados.get("forma_pagamento", "")
    ).strip()
    id_usuario = dados.get("id_usuario")
    id_categoria = dados.get("id_categoria")

    if not descricao:
        return jsonify({
            "erro": "A descrição é obrigatória."
        }), 400

    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return jsonify({
            "erro": "O valor deve ser numérico."
        }), 400

    if valor <= 0:
        return jsonify({
            "erro": "O valor deve ser maior que zero."
        }), 400

    if not data_gasto:
        return jsonify({
            "erro": "A data do gasto é obrigatória."
        }), 400

    if not forma_pagamento:
        return jsonify({
            "erro": "A forma de pagamento é obrigatória."
        }), 400

    try:
        id_usuario = int(id_usuario)
        id_categoria = int(id_categoria)
    except (TypeError, ValueError):
        return jsonify({
            "erro": "Usuário e categoria devem ser informados."
        }), 400

    try:
        with conectar_banco() as conexao:
            usuario = conexao.execute(
                """
                SELECT id_usuario
                FROM usuarios
                WHERE id_usuario = ?
                """,
                (id_usuario,)
            ).fetchone()

            if usuario is None:
                return jsonify({
                    "erro": "Usuário não encontrado."
                }), 404

            categoria = conexao.execute(
                """
                SELECT id_categoria
                FROM categorias
                WHERE id_categoria = ?
                """,
                (id_categoria,)
            ).fetchone()

            if categoria is None:
                return jsonify({
                    "erro": "Categoria não encontrada."
                }), 404

            cursor = conexao.execute(
                """
                INSERT INTO gastos (
                    descricao,
                    valor,
                    data_gasto,
                    forma_pagamento,
                    id_usuario,
                    id_categoria
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    descricao,
                    valor,
                    data_gasto,
                    forma_pagamento,
                    id_usuario,
                    id_categoria
                )
            )

            conexao.commit()
            novo_id = cursor.lastrowid

        return jsonify({
            "mensagem": "Gasto cadastrado com sucesso.",
            "id_gasto": novo_id
        }), 201

    except sqlite3.IntegrityError as erro:
        return jsonify({
            "erro": "Os dados informados violam as regras do banco.",
            "detalhes": str(erro)
        }), 400

    except sqlite3.Error as erro:
        return jsonify({
            "erro": "Não foi possível cadastrar o gasto.",
            "detalhes": str(erro)
        }), 500


@app.route("/gastos/<int:id_gasto>", methods=["DELETE"])
def excluir_gasto(id_gasto):
    try:
        with conectar_banco() as conexao:
            gasto = conexao.execute(
                """
                SELECT id_gasto
                FROM gastos
                WHERE id_gasto = ?
                """,
                (id_gasto,)
            ).fetchone()

            if gasto is None:
                return jsonify({
                    "erro": "Gasto não encontrado."
                }), 404

            conexao.execute(
                """
                DELETE FROM gastos
                WHERE id_gasto = ?
                """,
                (id_gasto,)
            )

            conexao.commit()

        return jsonify({
            "mensagem": "Gasto excluído com sucesso."
        }), 200

    except sqlite3.Error as erro:
        return jsonify({
            "erro": "Não foi possível excluir o gasto.",
            "detalhes": str(erro)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)