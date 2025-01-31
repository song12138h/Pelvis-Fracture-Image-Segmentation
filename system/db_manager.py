import pyodbc
from sqlalchemy import create_engine, Column, Integer, String, CHAR, VARCHAR, DateTime, Date, ForeignKey, Enum, Text
import pymysql
#from sqlalchemy import Column, Integer, String, create_engine, Float, ForeignKey, NCHAR, VARCHAR
from sqlalchemy.dialects.mysql import ENUM
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 数据库连接设置（MySQL）

#connection_string = "mysql+pymysql://root:hys12138@localhost:3306/pelvis"

# 创建 SQLAlchemy 引擎
#engine = create_engine(connection_string)

# 测试 SQLAlchemy 连接
# try:
#     with engine.connect() as connection:
#         print("SQLAlchemy 连接成功")
# except Exception as e:
#     print("SQLAlchemy 连接失败:", e)
#
# Session = sessionmaker(bind=engine)
# session = Session()

Base = declarative_base()

# 医生表
'''class Doctors(Base):
    __tablename__ = 'doctors'
    doctor_id = Column(String(20), primary_key=True)
    doctor_name = Column(String(50))
    doctor_password = Column(String(20))
    phone = Column(String(11))
    specialty = Column(String(50))'''

# 病人表
class patients(Base):
    __tablename__ = 'patients'
    # 定义表的字段
    patient_id = Column(String(6), primary_key=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum('male', 'female', 'other'), nullable=True)
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    phone_number = Column(String(20), nullable=True)
    age = Column(Integer, nullable=True)
    id_card = Column(String(18), nullable=True)
    patient_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)

    # 反向关系，表示一个病人有多个骨折历史
    fracturehistories = relationship("fracturehistories", back_populates="patients", cascade="all, delete")


class fracturehistories(Base):
    __tablename__ = 'fracturehistories'
    # 定义表的字段
    history_id = Column(String(6), primary_key=True, nullable=False)
    patient_id = Column(String(6), ForeignKey('patients.patient_id', ondelete="CASCADE", onupdate="RESTRICT"),
                        nullable=False)
    fracture_date = Column(Date, nullable=False)
    fracture_location = Column(Enum('pelvis', 'femur', 'spine', 'other'), nullable=False)
    severity_level = Column(Enum('mild', 'moderate', 'severe'), nullable=False)
    diagnosis_details = Column(Text, nullable=True)

    # 定义外键关系（可以用于查询相关患者信息）
    patients = relationship("patients", back_populates="fracturehistories")


# 管理员表
class Admin(Base):
    __tablename__ = 'admins'
    admin_id = Column(String(20), primary_key=True)
    admin_name = Column(String(50))
    admin_password = Column(String(20))
    phone = Column(String(11))

'''def verify_user(user_id, password, user_type):
    if user_type == 'doctor':
        user = session.query(Doctor).filter_by(doctor_id=user_id).first()
    elif user_type == 'patient':
        user = session.query(Patient).filter_by(patient_id=user_id).first()
    elif user_type == 'admin':
        user = session.query(Admin).filter_by(admin_id=user_id).first()
    else:
        return False, "无效的用户类型"

    if not user:
        return False, "用户不存在"

    if user_type == 'doctor':
        is_correct_password = user.doctor_password == password
    elif user_type == 'patient':
        is_correct_password = user.patient_password == password
    else:  # admin
        is_correct_password = user.admin_password == password

    if is_correct_password:
        return True, "登录成功"
    else:
        return False, "密码错误"
'''
'''def register_user(user_id, name, password, phone, user_type, specialty=None):
    if user_type == 'doctor':
        new_user = Doctor(doctor_id=user_id, doctor_name=name, doctor_password=password, phone=phone, specialty=specialty)
    elif user_type == 'patient':
        new_user = Patient(patient_id=user_id, patient_name=name, patient_password=password, phone=phone)
    elif user_type == 'admin':
        new_user = Admin(admin_id=user_id, admin_name=name, admin_password=password, phone=phone)
    else:
        return False, "无效的用户类型"
'''

import pymysql
from pymysql import Error
from db_config import db_config
import logging

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_connection():
    try:
        connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset=db_config['charset'],
            port=db_config['port']
        )
        logger.info("Successfully connected to MySQL database")
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None

def verify_user(user_id, password, user_type):
    try:
        connection = get_connection()
        if not connection:
            logger.error("Failed to establish database connection")
            return False, "数据库连接失败"
        
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        query = f"SELECT * FROM {user_type}s WHERE id = %s AND password = %s"
        logger.debug(f"Executing query: {query} with params: {user_id}, {password}")
        cursor.execute(query, (user_id, password))
        
        user = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if user:
            logger.info(f"User {user_id} successfully logged in")
            return True, "登录成功！"
        logger.warning(f"Failed login attempt for user {user_id}")
        return False, "用户名或密码错误"
        
    except Error as e:
        logger.error(f"Database error: {str(e)}")
        return False, "数据库错误"

'''def register_user(user_id, name, password, phone, user_type, specialty=None):
    try:
        connection = get_connection()
        if not connection:
            return False, "数据库连接失败"
            
        cursor = connection.cursor()
        
        if user_type == 'doctor':
            query = """INSERT INTO doctors 
                    (id, name, password, phone, specialty) 
                    VALUES (%s, %s, %s, %s, %s)"""
            values = (user_id, name, password, phone, specialty)
        else:
            query = f"""INSERT INTO {user_type}s 
                    (id, name, password, phone) 
                    VALUES (%s, %s, %s, %s)"""
            values = (user_id, name, password, phone)
            
        cursor.execute(query, values)
        connection.commit()
        
        cursor.close()
        connection.close()
        
        return True, "注册成功"
    except Exception as e:
        session.rollback()
        return False, f"数据库错误: {e}"
'''

# MySQL 数据库初始化函数
def init_database():
    try:

        # 首先创建数据库连接（不指定数据库名）
        conn_params = db_config.copy()
        conn_params.pop('database')  # 移除数据库名称
        
        connection = pymysql.connect(**conn_params)
        cursor = connection.cursor()
        
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {db_config['database']}")

        # 创建医生表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                password VARCHAR(100) NOT NULL,
                phone VARCHAR(20),
                specialty VARCHAR(50)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        # 创建病人表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id VARCHAR(6) PRIMARY KEY,
                patient_name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                phone_number VARCHAR(20),
                date_of_birth DATE,
                gender ENUM('male', 'female', 'other'),
                contact_person VARCHAR(100),
                contact_phone VARCHAR(20),
                email VARCHAR(100),
                age INT,
                id_card VARCHAR(18)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        # 创建骨折病历表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fracturehistories (
                history_id VARCHAR(6) PRIMARY KEY,
                patient_id VARCHAR(6) NOT NULL,
                fracture_date DATE NOT NULL,
                fracture_location ENUM('pelvis', 'femur', 'spine', 'other') NOT NULL,
                severity_level ENUM('mild', 'moderate', 'severe') NOT NULL,
                diagnosis_details TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
                    ON DELETE CASCADE
                    ON UPDATE RESTRICT
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)

        # 创建病人表
        # cursor.execute("""
        #     CREATE TABLE IF NOT EXISTS patients (
        #         id VARCHAR(20) PRIMARY KEY,
        #         name VARCHAR(50) NOT NULL,
        #         password VARCHAR(100) NOT NULL,
        #         phone VARCHAR(20)
        #     ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        # """)
        
        # 创建管理员表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id VARCHAR(20) PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                password VARCHAR(100) NOT NULL,
                phone VARCHAR(20)
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("Database initialized successfully")
        return True
        
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        return False

# 插入病人信息的函数
def insert_patient(patient_id, patient_name, password_hash, phone_number=None, date_of_birth=None,
                   gender=None, contact_person=None, contact_phone=None, email=None, age=None, id_card=None):
    """插入病人信息"""
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # 验证性别合法性
        if gender and gender not in ['male', 'female', 'other']:
            raise ValueError(f"Invalid gender: {gender}")

        # 插入数据的 SQL
        insert_query = """
        INSERT INTO patients (patient_id, patient_name, password_hash, phone_number, date_of_birth, gender, 
                              contact_person, contact_phone, email, age, id_card)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (patient_id, patient_name, password_hash, phone_number, date_of_birth,
                                      gender, contact_person, contact_phone, email, age, id_card))
        connection.commit()
        logger.info(f"Successfully inserted patient {patient_name} with ID {patient_id}.")
    except pymysql.MySQLError as e:
        logger.error(f"Error inserting patient: {e}")
    finally:
        cursor.close()
        connection.close()

def insert_fracture_history(history_id, patient_id, fracture_date, fracture_location, severity_level, diagnosis_details):
    """插入骨折病历信息"""
    try:
        connection = get_connection()
        cursor = connection.cursor()

        # 验证骨折位置和严重程度的合法性
        if fracture_location not in ['pelvis', 'femur', 'spine', 'other']:
            raise ValueError(f"Invalid fracture location: {fracture_location}")
        if severity_level not in ['mild', 'moderate', 'severe']:
            raise ValueError(f"Invalid severity level: {severity_level}")

        # 检查患者是否存在
        cursor.execute("SELECT patient_id FROM patients WHERE patient_id = %s", (patient_id,))
        if not cursor.fetchone():
            raise ValueError(f"Patient with ID {patient_id} does not exist.")

        # 插入数据的 SQL
        insert_query = """
        INSERT INTO fracturehistories (history_id, patient_id, fracture_date, fracture_location, severity_level, diagnosis_details)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (history_id, patient_id, fracture_date, fracture_location, severity_level, diagnosis_details))
        connection.commit()
        logger.info(f"Successfully inserted fracture history for patient ID {patient_id}.")
    except pymysql.MySQLError as e:
        logger.error(f"Error inserting fracture history: {e}")
    finally:
        cursor.close()
        connection.close()

# 示例：插入一条病人信息
insert_patient(
    patient_id="P00001",
    patient_name="张三",
    password_hash="hashed_password_123",
    phone_number="1234567890",
    date_of_birth="1985-06-15",
    gender="male",
    contact_person="李四",
    contact_phone="0987654321",
    email="zhangsan@example.com",
    age=38,
    id_card="123456789012345678"
)

# 示例：插入一条骨折病历信息
insert_fracture_history(
    history_id="F00001",
    patient_id="P00001",
    fracture_date="2024-06-15",
    fracture_location="pelvis",
    severity_level="moderate",
    diagnosis_details="Fracture at the pelvic region."
)
# 插入第一条病人信息
insert_patient(
    patient_id="P00002",
    patient_name="李四",
    password_hash="hashed_password_456",
    phone_number="2345678901",
    date_of_birth="1990-08-22",
    gender="female",
    contact_person="王五",
    contact_phone="9876543210",
    email="lisi@example.com",
    age=35,
    id_card="234567890123456789"
)

# 插入第一条骨折病历信息
insert_fracture_history(
    history_id="F00002",
    patient_id="P00002",
    fracture_date="2024-07-10",
    fracture_location="femur",
    severity_level="severe",
    diagnosis_details="Severe femur fracture due to accident."
)

# 插入第二条病人信息
insert_patient(
    patient_id="P00003",
    patient_name="王五",
    password_hash="hashed_password_789",
    phone_number="3456789012",
    date_of_birth="1987-02-18",
    gender="male",
    contact_person="赵六",
    contact_phone="8765432109",
    email="wangwu@example.com",
    age=38,
    id_card="345678901234567890"
)

# 插入第二条骨折病历信息
insert_fracture_history(
    history_id="F00003",
    patient_id="P00003",
    fracture_date="2024-07-20",
    fracture_location="spine",
    severity_level="mild",
    diagnosis_details="Mild spine fracture after a fall."
)

# 在程序启动时初始化数据库
if __name__ == "__main__":
    init_database()
