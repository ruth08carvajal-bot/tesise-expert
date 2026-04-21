import mysql.connector
conn = mysql.connector.connect(host='localhost', user='root', password='0', database='sis_expert_bd')
cursor = conn.cursor(dictionary=True)
cursor.execute('SELECT id_nino, id_user, id_tut, nombre FROM nino ORDER BY id_nino DESC LIMIT 5')
ninos = cursor.fetchall()
print('Últimos niños registrados:')
for n in ninos:
    print(f'ID: {n["id_nino"]}, id_user: {n["id_user"]}, id_tut: {n["id_tut"]}, nombre: {n["nombre"]}')
conn.close()