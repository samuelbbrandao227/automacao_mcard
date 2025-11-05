from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange

class RecargaForm(FlaskForm):
    forma_pagamento = SelectField(
        "Forma de Pagamento",
        choices=[("", "Selecione uma forma de pagamento"), ("PIX", "Pix"), ("DINHEIRO", "Dinheiro")],
        validators=[DataRequired(message="Escolha uma forma de pagamento")]
    )

    nome_pagador = StringField(
        "Nome do Pagador",
        validators=[Length(max=100)]
    )

    numero_cartao = StringField(
        "Número do Cartão (4 dígitos)",
        validators=[DataRequired(), Length(min=4, max=6)]
    )

    valor = DecimalField(
        "Valor da Recarga (R$)",
        validators=[DataRequired(), NumberRange(min=0.01)]
    )

    submit = SubmitField("Realizar Recarga")
