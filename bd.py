import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"

day_translation = {
    "monday": "segunda",
    "tuesday": "terça",
    "wednesday": "quarta",
    "thursday": "quinta",
    "friday": "sexta",
    "saturday": "sábado",
    "sunday": "domingo"
}

# Conexão com o banco de dados
def connect_db():
    return sqlite3.connect(DB_NAME)

# Função para criar tabelas
def create_tables():
    conn = connect_db()
    cursor = conn.cursor()

    # Tabela para alunos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            degree TEXT NOT NULL,
            image BLOB
        )
    ''')

    # Tabela para disciplinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS discipline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    ''')

    # Tabela associativa entre alunos e disciplinas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students_disciplines (
            student_id INTEGER NOT NULL,
            discipline_id INTEGER NOT NULL,
            PRIMARY KEY (student_id, discipline_id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (discipline_id) REFERENCES discipline(id)
        )
    ''')

    # Tabela para registros de presença
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            discipline_id INTEGER NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (discipline_id) REFERENCES discipline(id)
        )
    ''')

    conn.commit()
    conn.close()

# Função para cadastrar aluno
def register_student(student_id, name, degree, image_path):
    conn = connect_db()
    cursor = conn.cursor()
    with open(image_path, 'rb') as file:
        image_data = file.read()
    cursor.execute(
        "INSERT INTO students (id, name, degree, image) VALUES (?, ?, ?, ?)",
        (student_id, name, degree, image_data)
    )
    conn.commit()
    conn.close()

# Função para cadastrar matéria
def register_discipline(name, day_of_week, start_time, end_time):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO discipline (name, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
        (name, day_of_week, start_time, end_time)
    )
    conn.commit()
    conn.close()

# Função para verificar dia e horário de uma matéria
def is_valid_discipline(discipline_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT day_of_week, start_time, end_time FROM discipline WHERE id = ?", (discipline_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        day_of_week, start_time, end_time = result
        current_day = datetime.now().strftime("%A").lower()
        current_day = day_translation.get(current_day)
        current_time = datetime.now().strftime("%H:%M")
        # Verificar se o dia e o horário correspondem
        if current_day == day_of_week.lower() and start_time <= current_time <= end_time:
            return True
    return False

def add_student_to_discipline(student_id, discipline_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO students_disciplines (student_id, discipline_id) VALUES (?, ?)",
            (student_id, discipline_id)
        )
        conn.commit()
        print(f"Aluno {student_id} adicionado à disciplina {discipline_id}.")
    except sqlite3.IntegrityError:
        print("Este aluno já está associado a essa disciplina.")
    conn.close()

# Função para registrar presença
def register_attendance(student_id, discipline_id):
    # Verificar se o aluno está inscrito na disciplina
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM students_disciplines
        WHERE student_id = ? AND discipline_id = ?
    ''', (student_id, discipline_id))
    is_enrolled = cursor.fetchone()[0]
    conn.close()

    if not is_enrolled:
        print("O aluno não está inscrito nesta disciplina.")
        return 1  # Código para aluno não inscrito

    # Verificar se o dia e o horário estão corretos
    if is_valid_discipline(discipline_id):
        conn = connect_db()
        cursor = conn.cursor()

        # Obter a data atual no formato YYYY-MM-DD
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Verificar se já existe presença registrada para o aluno na matéria no mesmo dia
        cursor.execute('''
            SELECT COUNT(*) FROM attendance
            WHERE student_id = ? AND discipline_id = ? AND DATE(timestamp) = ?
        ''', (student_id, discipline_id, current_date))
        result = cursor.fetchone()

        if result[0] > 0:
            print("A presença já foi registrada hoje para este aluno e matéria.")
            conn.close()
            return 3
        else:
            # Registrar presença
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO attendance (student_id, discipline_id, timestamp) VALUES (?, ?, ?)",
                (student_id, discipline_id, timestamp)
            )
            conn.commit()
            print(f"Presença registrada para o aluno {student_id} na matéria {discipline_id}.")
            conn.close()
            return 2
    else:
        print("A presença não pode ser registrada. O dia ou horário não corresponde à matéria.")
        return 4


# Função para buscar matérias
def fetch_disciplines():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, day_of_week, start_time, end_time FROM discipline")
    disciplines = cursor.fetchall()
    conn.close()
    return disciplines

# Função para buscar alunos
def fetch_students():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, degree FROM students")
    students = cursor.fetchall()
    conn.close()
    return students

def fetch_student(id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, degree, image FROM students WHERE id = ?", (id,))
    student = cursor.fetchone()
    conn.close()
    return student

def fetch_disciplines_by_student(student_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT d.id, d.name, d.day_of_week, d.start_time, d.end_time
        FROM discipline d
        INNER JOIN students_disciplines sd ON d.id = sd.discipline_id
        WHERE sd.student_id = ?
    ''', (student_id,))
    disciplines = cursor.fetchall()
    conn.close()
    return disciplines

def fetchDisciplineByHourAndDay(student_id, day, hour):
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()

        query = """
            SELECT d.id
            FROM discipline d
            INNER JOIN students_disciplines sd ON d.id = sd.discipline_id
            WHERE sd.student_id = ?
            AND d.day_of_week = ?
            AND d.start_time <= ?
            AND d.end_time > ?
        """

        cursor.execute(query, (student_id, day, hour, hour))
        discipline_id = cursor.fetchone()
        conn.close()

        if discipline_id:
            return discipline_id[0]
        else:
            return None

    except Exception as e:
        print(f"Erro ao buscar disciplina: {e}")
        return None


def criarBanco():
    create_tables()
    register_discipline("Banco de Dados 2", "terça", "12:00", "20:00")
    register_discipline("Compiladores", "terça", "12:00", "20:00")
    register_discipline("Mostra de Trabalhos Cientificos", "sexta", "10:00", "23:00")
    register_student(16749856, "Marco Vinicius", "Ciencia da Computacao", "Images/16749856.jpg")
    register_student(745932625, "Victor Zucherato", "Ciencia da Computacao", "Images/745932625.jpeg")

    # Associar alunos a disciplinas
    add_student_to_discipline(16749856, 1)
    add_student_to_discipline(745932625, 2)

#criarBanco()