from db import criar_tabela, inserir_motor, motor_existe

def popular_banco():
    criar_tabela()
    
    # Dados de exemplo (Tuplas de 17 campos)
    motores_demo = [
        ("WEG", "W22 IR3", "132M", 85.0, 10.0, "cv", 380.0, 15.2, 4, 0.82, 1750, "IP55", "F", 1.15, "Ar", "Estrela", "images/weg1.png"),
        ("VOGES", "V-Line", "90S", 22.0, 2.0, "cv", 220.0, 6.1, 2, 0.85, 3450, "IP21", "B", 1.0, "Ar", "Triângulo", "images/voges1.png")
    ]

    for motor in motores_demo:
        # Verifica se já existe para não duplicar toda vez que rodar
        if not motor_existe(motor[0], motor[1], motor[4], motor[6]):
            inserir_motor(motor)
            print(f"Motor {motor[1]} inserido!")
        else:
            print(f"Motor {motor[1]} já existe no banco.")

if __name__ == "__main__":
    popular_banco()