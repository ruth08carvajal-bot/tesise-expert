-- MySQL dump 10.13  Distrib 8.0.19, for Win64 (x86_64)
--
-- Host: localhost    Database: sis_expert_bd
-- ------------------------------------------------------
-- Server version	12.2.2-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `id_adm` int(11) NOT NULL AUTO_INCREMENT,
  `id_user` int(11) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `cargo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_adm`),
  UNIQUE KEY `id_user` (`id_user`),
  CONSTRAINT `1` FOREIGN KEY (`id_user`) REFERENCES `usuario` (`id_user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `anamnesis_hechos`
--

DROP TABLE IF EXISTS `anamnesis_hechos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `anamnesis_hechos` (
  `id_ana_h` int(11) NOT NULL AUTO_INCREMENT,
  `id_nino` int(11) DEFAULT NULL,
  `id_hecho` int(11) DEFAULT NULL,
  `valor_presencia` tinyint(4) DEFAULT 1,
  PRIMARY KEY (`id_ana_h`),
  KEY `id_nino` (`id_nino`),
  KEY `id_hecho` (`id_hecho`),
  CONSTRAINT `1` FOREIGN KEY (`id_nino`) REFERENCES `nino` (`id_nino`) ON DELETE CASCADE,
  CONSTRAINT `2` FOREIGN KEY (`id_hecho`) REFERENCES `base_hechos` (`id_hecho`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `anamnesis_hechos`
--

LOCK TABLES `anamnesis_hechos` WRITE;
/*!40000 ALTER TABLE `anamnesis_hechos` DISABLE KEYS */;
/*!40000 ALTER TABLE `anamnesis_hechos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_hechos`
--

DROP TABLE IF EXISTS `base_hechos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `base_hechos` (
  `id_hecho` int(11) NOT NULL,
  `cod_h` varchar(10) DEFAULT NULL,
  `descripcion` text NOT NULL,
  `categoria_clinica` varchar(50) DEFAULT NULL,
  `instrumento_origen` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_hecho`),
  UNIQUE KEY `cod_h` (`cod_h`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `base_hechos`
--

LOCK TABLES `base_hechos` WRITE;
/*!40000 ALTER TABLE `base_hechos` DISABLE KEYS */;
INSERT INTO `base_hechos` VALUES (1,'H001','Precisión en /r/','Fonologico','PEFF'),(2,'H002','Precisión en /rr/','Fonologico','PEFF'),(3,'H003','Precisión en /s/','Fonologico','PEFF'),(4,'H004','Precisión en /l/','Fonologico','PEFF'),(5,'H005','Precisión en /k/','Fonologico','PEFF'),(6,'H006','Precisión en /t/','Fonologico','PEFF'),(7,'H007','Precisión en /d/','Fonologico','PEFF'),(8,'H008','Precisión en /p/','Fonologico','PEFF'),(9,'H009','Precisión en /b/','Fonologico','PEFF'),(10,'H010','Precisión en /g/','Fonologico','PEFF'),(11,'H011','Precisión en /m/','Fonologico','PEFF'),(12,'H012','Precisión en /n/','Fonologico','PEFF'),(13,'H013','Precisión en /ñ/','Fonologico','PEFF'),(14,'H014','Precisión en /f/','Fonologico','PEFF'),(15,'H015','Precisión en /j/','Fonologico','PEFF'),(16,'H016','Precisión en /ch/','Fonologico','PEFF'),(17,'H017','Precisión en /y/','Fonologico','PEFF'),(18,'H018','Precisión en /x/','Fonologico','PEFF'),(19,'H019','Precisión en grupos consonánticos','Fonologico','PEFF'),(20,'H020','Omisión de fonemas','Error','PEFF'),(21,'H021','Sustitución de fonemas','Error','PEFF'),(22,'H022','Distorsión de fonemas','Error','PEFF'),(23,'H023','Inconsistencia en errores','Error','PEFF'),(24,'H024','Inteligibilidad (%)','General','PEFF'),(25,'H025','Dificultad en diadococinesia','Motor','PEFF'),(26,'H026','Dificultad en praxias orales','Motor','PEFF'),(27,'H027','Alteración en estructuras anatómicas','Estructural','PEFF'),(28,'H028','Dificultad repetición sílabas CV','Articulacion','TAR'),(29,'H029','Dificultad repetición sílabas CVC','Articulacion','TAR'),(30,'H030','Dificultad palabras bisílabas','Articulacion','TAR'),(31,'H031','Dificultad palabras trisílabas','Articulacion','TAR'),(32,'H032','Dificultad palabras polisílabas','Articulacion','TAR'),(33,'H033','Simplificación grupos consonánticos','Fonologico','TAR'),(34,'H034','Reducción de sílabas','Fonologico','TAR'),(35,'H035','Vocabulario receptivo (percentil)','Lenguaje','TEVI-R'),(36,'H036','Vocabulario receptivo < p25','Lenguaje','TEVI-R'),(37,'H037','Vocabulario receptivo < p10','Lenguaje','TEVI-R'),(38,'H038','Vocabulario expresivo (percentil)','Lenguaje','TEVI-R'),(39,'H039','Vocabulario expresivo < p25','Lenguaje','TEVI-R'),(40,'H040','Vocabulario expresivo < p10','Lenguaje','TEVI-R'),(41,'H041','Discrepancia receptivo-expresivo > 20%','Lenguaje','TEVI-R'),(42,'H042','Forma morfosintaxis percentil','Lenguaje','PLON-R'),(43,'H043','Forma < p10','Lenguaje','PLON-R'),(44,'H044','Contenido semántica percentil','Lenguaje','PLON-R'),(45,'H045','Contenido < p10','Lenguaje','PLON-R'),(46,'H046','Uso pragmática percentil','Lenguaje','PLON-R'),(47,'H047','Uso < p10','Lenguaje','PLON-R'),(48,'H048','Longitud media enunciado (LME)','Lenguaje','PLON-R'),(49,'H049','LME < esperado','Lenguaje','PLON-R'),(50,'H050','Morfosintaxis (BLOC) percentil','Lenguaje','BLOC'),(51,'H051','Morfosintaxis < p10','Lenguaje','BLOC'),(52,'H052','Semántica (BLOC) percentil','Lenguaje','BLOC'),(53,'H053','Semántica < p10','Lenguaje','BLOC'),(54,'H054','Fonología (BLOC) percentil','Lenguaje','BLOC'),(55,'H055','Fonología < p10','Lenguaje','BLOC'),(56,'H056','Pragmática (BLOC) percentil','Lenguaje','BLOC'),(57,'H057','Pragmática < p10','Lenguaje','BLOC'),(58,'H058','Dificultad comprensión oraciones','Lenguaje','BLOC'),(59,'H059','Dificultad producción oraciones','Lenguaje','BLOC'),(60,'H060','Recepción auditiva (percentil)','Procesamiento','ITPA'),(61,'H061','Recepción visual (percentil)','Procesamiento','ITPA'),(62,'H062','Asociación auditiva (percentil)','Procesamiento','ITPA'),(63,'H063','Asociación visual (percentil)','Procesamiento','ITPA'),(64,'H064','Expresión verbal (percentil)','Procesamiento','ITPA'),(65,'H065','Expresión motora (percentil)','Procesamiento','ITPA'),(66,'H066','Memoria secuencial auditiva (p)','Procesamiento','ITPA'),(67,'H067','Memoria secuencial visual (p)','Procesamiento','ITPA'),(68,'H068','Discrepancia auditivo-visual','Procesamiento','ITPA'),(69,'H069','Groping (búsqueda articulatoria)','Motor','TSA'),(70,'H070','Repeticiones de sílabas','Fluidez','SSI-4'),(71,'H071','Prolongaciones','Fluidez','SSI-4'),(72,'H072','Bloqueos','Fluidez','SSI-4'),(73,'H073','Duración disfluencias','Fluidez','SSI-4'),(74,'H074','Severidad tartamudez','Fluidez','SSI-4'),(75,'H075','Evitación de palabras','Fluidez','SSI-4'),(76,'H076','Ansiedad al hablar','Fluidez','SSI-4'),(77,'H077','Fluidez semántica (#palabras)','Lenguaje','Fluidez Verbal'),(78,'H078','Fluidez fonológica (#palabras)','Lenguaje','Fluidez Verbal'),(79,'H079','Fluidez semántica < p10','Lenguaje','Fluidez Verbal'),(80,'H080','Fluidez fonológica < p10','Lenguaje','Fluidez Verbal'),(81,'H081','Dificultad lectura palabras','Lectura','PROLEC-R'),(82,'H082','Dificultad lectura pseudopalabras','Lectura','PROLEC-R'),(83,'H083','Confusión letras similares','Lectura','PROLEC-R'),(84,'H084','Dificultad comprensión lectora','Lectura','PROLEC-R'),(85,'H085','Velocidad lectora (ppm)','Lectura','PROLEC-R'),(86,'H086','Velocidad < esperado','Lectura','PROLEC-R'),(87,'H087','Dificultad escritura dictado','Escritura','PROLEC-R'),(88,'H088','Omisiones en escritura','Escritura','PROLEC-R'),(89,'H089','Inversiones en escritura','Escritura','PROLEC-R'),(90,'H090','Dificultad copia textos','Escritura','PROLEC-R'),(91,'H091','Ronquera','Voz','VOZ'),(92,'H092','Afonía','Voz','VOZ'),(93,'H093','Tensión vocal','Voz','VOZ'),(94,'H094','Fatiga vocal','Voz','VOZ'),(95,'H095','Nódulos vocales','Voz','VOZ'),(96,'H096','Disfonía funcional','Voz','VOZ'),(97,'H097','Disfonía orgánica','Voz','VOZ'),(98,'H098','Dificultad filtrado auditivo','Procesamiento','SCAN-3'),(99,'H099','Dificultad escucha dicótica','Procesamiento','SCAN-3'),(100,'H100','Dificultad discriminación auditiva','Procesamiento','SCAN-3'),(101,'H101','TPAC Confirmado','Procesamiento','SCAN-3'),(102,'H102','Edad en meses','Demografico','Registro'),(103,'H103','Rango 36-47 meses','Demografico','Registro'),(104,'H104','Rango 48-59 meses','Demografico','Registro'),(105,'H105','Rango 60-71 meses','Demografico','Registro'),(106,'H106','Rango 72-83 meses','Demografico','Registro'),(107,'H107','Rango 84-95 meses','Demografico','Registro'),(108,'H108','Rango 96-107 meses','Demografico','Registro'),(109,'H109','Rango 108-120 meses','Demografico','Registro'),(110,'H110','Sexo masculino','Demografico','Registro'),(111,'H111','Sexo femenino','Demografico','Registro'),(112,'H112','Contexto cultural paceño','Demografico','Registro'),(113,'H113','Ausencia vibración lingual','Anamnesis','Tutor'),(114,'H114','Dificultad órdenes con ruido','Anamnesis','Tutor'),(115,'H115','Errores lectura fluida','Anamnesis','Tutor'),(116,'H116','Antecedentes familiares','Anamnesis','Tutor'),(117,'H117','Otitis frecuentes','Anamnesis','Tutor'),(118,'H118','Complicaciones parto','Anamnesis','Tutor'),(119,'H119','Bilingüismo familiar','Anamnesis','Tutor'),(120,'H120','Uso prolongado chupón','Anamnesis','Tutor'),(121,'H121','Dificultad masticación','Anamnesis','Tutor'),(122,'H122','Respiración bucal','Anamnesis','Tutor'),(123,'H123','Muda de dientes incisivos','Anamnesis','Tutor'),(124,'H124','Evitación contacto social','Anamnesis','Tutor'),(125,'H125','Errores constantes escritura','Anamnesis','Tutor'),(126,'H126','Conciencia de error','Anamnesis','Tutor'),(127,'H127','Hipotonía o debilidad muscular facial','Motor','Observación'),(128,'H128','Dificultad en control de la postura/babeo','Motor','Anamnesis'),(129,'H129','Errores en el trazo de letras (caligrafía)','Escritura','PROLEC-R'),(130,'H130','Postura inadecuada al escribir','Escritura','Observación'),(131,'H131','Omisión de reglas de acentuación/puntuación','Ortografía','Dictado'),(132,'H132','Sustitución de letras con sonido similar (v/b)','Ortografía','Dictado'),(133,'H133','Dificultad para mantener contacto visual','Pragmático','Social'),(134,'H134','Dificultad para respetar turnos de habla','Pragmático','Social'),(135,'H135','Interpretación literal (no entiende bromas)','Pragmático','Social'),(136,'H136','Dificultad en reproducción de ritmos (golpes)','Ritmo','Nieto Herrera'),(137,'H137','Incapacidad de reconocer onomatopeyas','Auditivo','Nieto Herrera'),(138,'H138','Dificultad en seriación visual (colores/formas)','Cognitivo','Nieto Herrera'),(139,'H139','Falla en esquema corporal (señalar partes)','Esquema Corporal','Nieto Herrera'),(140,'H140','Dificultad en lateralidad (mano derecha/izquierda)','Psicomotriz','Nieto Herrera');
/*!40000 ALTER TABLE `base_hechos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `base_reglas`
--

DROP TABLE IF EXISTS `base_reglas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `base_reglas` (
  `id_regla` int(11) NOT NULL AUTO_INCREMENT,
  `id_hecho` int(11) DEFAULT NULL,
  `id_diag` int(11) DEFAULT NULL,
  `peso_certeza` float DEFAULT NULL,
  `id_ejercicio_sugerido` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_regla`),
  KEY `id_hecho` (`id_hecho`),
  KEY `id_diag` (`id_diag`),
  KEY `id_ejercicio_sugerido` (`id_ejercicio_sugerido`),
  CONSTRAINT `1` FOREIGN KEY (`id_hecho`) REFERENCES `base_hechos` (`id_hecho`),
  CONSTRAINT `2` FOREIGN KEY (`id_diag`) REFERENCES `catalogo_diagnosticos` (`id_diag`),
  CONSTRAINT `3` FOREIGN KEY (`id_ejercicio_sugerido`) REFERENCES `catalogo_ejercicios` (`id_ejercicio`)
) ENGINE=InnoDB AUTO_INCREMENT=210 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `base_reglas`
--

LOCK TABLES `base_reglas` WRITE;
/*!40000 ALTER TABLE `base_reglas` DISABLE KEYS */;
INSERT INTO `base_reglas` VALUES (135,1,1,0.4,1),(136,26,1,0.3,7),(137,25,1,0.3,NULL),(138,127,2,0.4,NULL),(139,25,2,0.3,NULL),(140,128,2,0.3,8),(141,4,3,0.5,3),(142,13,3,0.5,2),(143,4,4,1,3),(144,103,5,0.6,NULL),(145,1,5,0.4,1),(146,28,6,0.5,NULL),(147,26,6,0.5,7),(148,91,7,1,NULL),(149,122,8,0.7,5),(150,27,8,0.3,NULL),(151,9,9,1,NULL),(152,122,10,0.6,5),(153,10,10,0.4,NULL),(154,137,11,0.5,9),(155,49,11,0.5,NULL),(156,138,12,0.4,NULL),(157,43,12,0.6,NULL),(158,117,13,0.7,NULL),(159,100,13,0.3,20),(160,136,14,0.4,4),(161,137,14,0.3,9),(162,49,14,0.3,NULL),(163,133,15,0.5,18),(164,134,15,0.5,19),(165,77,16,0.6,11),(166,53,16,0.4,13),(167,11,17,0.5,NULL),(168,118,17,0.5,NULL),(169,58,18,0.5,12),(170,48,18,0.5,16),(171,66,19,1,NULL),(172,59,20,1,NULL),(173,82,21,0.7,14),(174,115,21,0.3,NULL),(175,83,22,0.6,15),(176,81,22,0.4,NULL),(177,129,23,0.5,NULL),(178,139,23,0.5,6),(179,131,24,0.6,17),(180,132,24,0.4,NULL),(181,136,25,1,4),(182,139,26,0.5,6),(183,140,26,0.5,NULL),(184,107,27,0.6,NULL),(185,136,27,0.4,4),(186,129,28,0.5,NULL),(187,131,28,0.5,17),(188,82,29,0.5,14),(189,83,29,0.5,15),(190,90,30,1,NULL),(191,70,31,0.5,NULL),(192,71,31,0.5,NULL),(193,32,32,0.6,2),(194,136,32,0.4,4),(195,73,33,1,NULL),(196,98,34,0.5,NULL),(197,100,34,0.5,20),(198,3,35,0.5,3),(199,21,35,0.5,NULL),(200,135,36,0.5,10),(201,16,36,0.5,NULL),(202,12,37,0.5,NULL),(203,1,37,0.5,1),(204,124,38,0.7,NULL),(205,76,38,0.3,NULL),(206,136,39,0.3,4),(207,139,39,0.3,6),(208,140,39,0.4,NULL),(209,84,40,1,NULL);
/*!40000 ALTER TABLE `base_reglas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `catalogo_diagnosticos`
--

DROP TABLE IF EXISTS `catalogo_diagnosticos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `catalogo_diagnosticos` (
  `id_diag` int(11) NOT NULL,
  `nombre_diag` varchar(100) NOT NULL,
  `definicion_sencilla` text DEFAULT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_diag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `catalogo_diagnosticos`
--

LOCK TABLES `catalogo_diagnosticos` WRITE;
/*!40000 ALTER TABLE `catalogo_diagnosticos` DISABLE KEYS */;
INSERT INTO `catalogo_diagnosticos` VALUES (1,'Apraxia del Habla Infantil (AHI)','Dificultad para planificar y secuenciar los movimientos del habla.','Habla'),(2,'Disartria Pediátrica','Debilidad o falta de control en los músculos del habla (asociado a hipotonía).','Habla'),(3,'Trastorno Fonológico','Dificultad para organizar los sonidos dentro de las palabras.','Habla'),(4,'Dislalia Funcional','Error en la articulación de fonemas específicos (ej. rotacismo).','Habla'),(5,'Retraso del Habla','Desarrollo de la articulación más lento que lo esperado para su edad.','Habla'),(6,'Inmadurez Articulatoria','Persistencia de errores de articulación propios de niños más pequeños.','Habla'),(7,'Disfonía Infantil','Alteración en la calidad de la voz (ronquera o esfuerzo vocal).','Voz'),(8,'Rinolalia','Alteración del sonido por exceso o falta de aire por la nariz.','Habla'),(9,'Trastorno de la Prosodia','Alteración en el ritmo, acento o entonación al hablar.','Habla'),(10,'Incoordinación Fono-Respiratoria','Dificultad para coordinar la respiración con la emisión de voz.','Habla'),(11,'Retardo Primario del Lenguaje','Retraso en la aparición del lenguaje sin causa orgánica.','Lenguaje'),(12,'Disfasia (Trastorno Específico del Lenguaje)','Afectación grave en la adquisición y estructura del lenguaje.','Lenguaje'),(13,'Retardo Secundario a Déficit Sensorial','Dificultad lingüística derivada de una pérdida auditiva.','Lenguaje'),(14,'Retraso Simple del Lenguaje (RSL)','Desfase cronológico que afecta todos los niveles del lenguaje.','Lenguaje'),(15,'Trastorno Pragmático','Dificultad en el uso social del lenguaje y reglas de conversación.','Lenguaje'),(16,'Trastorno Semántico','Dificultad para comprender conceptos y relaciones entre palabras.','Lenguaje'),(17,'Afasia Infantil Adquirida','Pérdida del lenguaje tras un daño cerebral.','Lenguaje'),(18,'Trastorno Mixto Receptivo-Expresivo','Falla tanto en la comprensión como en la producción del lenguaje.','Lenguaje'),(19,'Déficit de Memoria Auditiva','Dificultad para retener y procesar información hablada.','Lenguaje'),(20,'Retraso en la Estructuración Sintáctica','Dificultad para armar oraciones correctamente según la edad.','Lenguaje'),(21,'Dislexia Fonológica','Dificultad para convertir letras en sonidos.','Lectura'),(22,'Dislexia Superficial','Dificultad para reconocer palabras de forma visual.','Lectura'),(23,'Disgrafía Motriz','Mala caligrafía debido a dificultades psicomotoras.','Escritura'),(24,'Disortografía','Dificultad para aplicar las reglas de escritura y ortografía.','Escritura'),(25,'Trastorno de la Percepción Temporal','Dificultad en el manejo del ritmo y secuencias temporales.','Percepción'),(26,'Trastorno de la Orientación Espacial','Confusión en la lateralidad y posición de las letras.','Percepción'),(27,'Retraso Lector Madurativo','Lentitud en el proceso lector por falta de madurez sensorial.','Lectura'),(28,'Disgrafía Mixta','Errores tanto en el trazo como en la composición de palabras.','Escritura'),(29,'Dislexia Mixta','Afectación tanto de la ruta fonológica como visual.','Lectura'),(30,'Agrafía Infantil','Incapacidad total o parcial para escribir tras un aprendizaje previo.','Escritura'),(31,'Tartamudez (Disfemia)','Interrupciones involuntarias en la fluidez del habla.','Fluidez'),(32,'Taquifemia','Habla demasiado rápida que afecta la claridad.','Fluidez'),(33,'Bradifemia','Habla excesivamente lenta.','Fluidez'),(34,'Trastorno de Procesamiento Auditivo Central (TPAC)','Dificultad para entender el habla en entornos con ruido.','Procesamiento'),(35,'Cuadro Mixto: Fonológico-Lector','Problemas de habla que complican el aprendizaje de lectura.','Mixto'),(36,'Cuadro Mixto: Pragmático-Semántico','Falla en el significado y en el uso social de la comunicación.','Mixto'),(37,'Disfasia con componente Apráxico','Trastorno de lenguaje sumado a falla de planificación motora.','Mixto'),(38,'Mutismo Selectivo','Inhibición del habla en situaciones sociales específicas.','Psicógeno'),(39,'Retardo Global de Maduración','Afectación conjunta de ritmo, lateralidad y lenguaje.','Mixto'),(40,'Dificultad de Comprensión Lectora','El niño lee bien pero no entiende el mensaje del texto.','Lectura');
/*!40000 ALTER TABLE `catalogo_diagnosticos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `catalogo_ejercicios`
--

DROP TABLE IF EXISTS `catalogo_ejercicios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `catalogo_ejercicios` (
  `id_ejercicio` int(11) NOT NULL,
  `nombre_ejercicio` varchar(100) DEFAULT NULL,
  `descripcion_instrucciones` text DEFAULT NULL,
  `nivel_dificultad` enum('Bajo','Medio','Alto') DEFAULT NULL,
  `tipo_apoyo` varchar(50) DEFAULT NULL,
  `id_hecho_objetivo` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_ejercicio`),
  KEY `id_hecho_objetivo` (`id_hecho_objetivo`),
  CONSTRAINT `1` FOREIGN KEY (`id_hecho_objetivo`) REFERENCES `base_hechos` (`id_hecho`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `catalogo_ejercicios`
--

LOCK TABLES `catalogo_ejercicios` WRITE;
/*!40000 ALTER TABLE `catalogo_ejercicios` DISABLE KEYS */;
INSERT INTO `catalogo_ejercicios` VALUES (1,'Palabra Corta','Repite: \"Tren\", \"Sol\", \"Flor\".','Bajo','MFCC',1),(2,'Palabra Compleja','Repite: \"Ferrocarril\", \"Trabalenguas\".','Alto','MFCC',13),(3,'Fonemas Aislados','Haz el sonido: /ssss/, /rrrr/, /chchch/.','Medio','MFCC',4),(4,'El Ritmo de Osito','El niño debe seguir un ritmo de golpes dado por el sistema. ¿Lo hizo bien?','Medio','Fuzzy-Padre',136),(5,'Soplo Controlado','Pide al niño que sople una vela o papel. ¿Tiene fuerza en el soplo?','Bajo','Fuzzy-Padre',122),(6,'Esquema Corporal','¿Identifica correctamente derecha, izquierda, arriba y abajo?','Alto','Fuzzy-Padre',139),(7,'Praxias Linguales','¿Mueve la lengua hacia arriba, abajo y a los lados con facilidad?','Bajo','Fuzzy-Padre',26),(8,'Control de Babeo','¿El niño presenta babeo constante o dificultad al tragar?','Bajo','Fuzzy-Padre',128),(9,'Onomatopeyas','Escucha el sonido: ¿Qué animal o cosa hace este ruido?','Bajo','Selección',137),(10,'Absurdos Visuales','Mira el dibujo: ¿Qué es lo que no tiene sentido en esta imagen?','Medio','Selección',135),(11,'Categorización','De este grupo de objetos: ¿Cuál es el que no pertenece?','Medio','Selección',77),(12,'Comprensión Auditiva','Escucha el cuento corto y elige la imagen que representa lo que pasó.','Alto','Selección',58),(13,'Opuestos','Si este objeto es grande, ¿cuál de estos es el pequeño?','Bajo','Selección',53),(14,'Ruta Fonológica','Lee la siguiente palabra inventada: \"Pli-tro\".','Alto','MFCC',82),(15,'Orientación Letras','Selecciona la letra \"d\" correcta entre las opciones.','Medio','Selección',83),(16,'Completar Frase','\"El perro _____ un hueso\". Selecciona la palabra que falta.','Alto','Selección',48),(17,'Reglas Ortográficas','¿Cuál de estas dos palabras está escrita correctamente?','Alto','Selección',131),(18,'Emociones','Mira la foto: ¿Cómo crees que se siente el niño?','Medio','Selección',133),(19,'Turnos de Habla','¿El niño suele interrumpir o respeta los turnos al conversar?','Bajo','Fuzzy-Padre',134),(20,'Atención Auditiva','¿El niño voltea o responde de inmediato cuando se le llama?','Bajo','Fuzzy-Padre',100);
/*!40000 ALTER TABLE `catalogo_ejercicios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `evaluacion_sesion`
--

DROP TABLE IF EXISTS `evaluacion_sesion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `evaluacion_sesion` (
  `id_ev` int(11) NOT NULL AUTO_INCREMENT,
  `id_nino` int(11) DEFAULT NULL,
  `fecha_eval` timestamp NULL DEFAULT current_timestamp(),
  `diagnostico_sistema` text DEFAULT NULL,
  `pronostico_sistema` text DEFAULT NULL,
  `sugerencia_ejercicios` text DEFAULT NULL,
  `explicacion_logica` text DEFAULT NULL,
  `notas_tutor` text DEFAULT NULL,
  `tipo_evaluacion` enum('Inicial','Control','Final') DEFAULT 'Control',
  PRIMARY KEY (`id_ev`),
  KEY `id_nino` (`id_nino`),
  CONSTRAINT `1` FOREIGN KEY (`id_nino`) REFERENCES `nino` (`id_nino`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `evaluacion_sesion`
--

LOCK TABLES `evaluacion_sesion` WRITE;
/*!40000 ALTER TABLE `evaluacion_sesion` DISABLE KEYS */;
/*!40000 ALTER TABLE `evaluacion_sesion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ficha_antecedentes`
--

DROP TABLE IF EXISTS `ficha_antecedentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ficha_antecedentes` (
  `id_nino` int(11) NOT NULL,
  `historia_clinica` text DEFAULT NULL,
  PRIMARY KEY (`id_nino`),
  CONSTRAINT `1` FOREIGN KEY (`id_nino`) REFERENCES `nino` (`id_nino`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ficha_antecedentes`
--

LOCK TABLES `ficha_antecedentes` WRITE;
/*!40000 ALTER TABLE `ficha_antecedentes` DISABLE KEYS */;
/*!40000 ALTER TABLE `ficha_antecedentes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `memoria_trabajo`
--

DROP TABLE IF EXISTS `memoria_trabajo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `memoria_trabajo` (
  `id_mem` int(11) NOT NULL AUTO_INCREMENT,
  `id_ev` int(11) DEFAULT NULL,
  `id_hecho` int(11) DEFAULT NULL,
  `valor_obtenido` float DEFAULT NULL,
  PRIMARY KEY (`id_mem`),
  KEY `id_ev` (`id_ev`),
  KEY `id_hecho` (`id_hecho`),
  CONSTRAINT `1` FOREIGN KEY (`id_ev`) REFERENCES `evaluacion_sesion` (`id_ev`) ON DELETE CASCADE,
  CONSTRAINT `2` FOREIGN KEY (`id_hecho`) REFERENCES `base_hechos` (`id_hecho`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `memoria_trabajo`
--

LOCK TABLES `memoria_trabajo` WRITE;
/*!40000 ALTER TABLE `memoria_trabajo` DISABLE KEYS */;
/*!40000 ALTER TABLE `memoria_trabajo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `nino`
--

DROP TABLE IF EXISTS `nino`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `nino` (
  `id_nino` int(11) NOT NULL AUTO_INCREMENT,
  `id_user` int(11) DEFAULT NULL,
  `id_tut` int(11) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `f_nac` date NOT NULL,
  `genero` varchar(15) DEFAULT NULL,
  `escolaridad` varchar(100) DEFAULT NULL,
  `parentesco` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id_nino`),
  UNIQUE KEY `id_user` (`id_user`),
  KEY `id_tut` (`id_tut`),
  CONSTRAINT `1` FOREIGN KEY (`id_user`) REFERENCES `usuario` (`id_user`),
  CONSTRAINT `2` FOREIGN KEY (`id_tut`) REFERENCES `tutor` (`id_tut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nino`
--

LOCK TABLES `nino` WRITE;
/*!40000 ALTER TABLE `nino` DISABLE KEYS */;
/*!40000 ALTER TABLE `nino` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `progreso_nino`
--

DROP TABLE IF EXISTS `progreso_nino`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `progreso_nino` (
  `id_progreso` int(11) NOT NULL AUTO_INCREMENT,
  `id_nino` int(11) DEFAULT NULL,
  `id_ejercicio` int(11) DEFAULT NULL,
  `fecha_realizacion` timestamp NULL DEFAULT current_timestamp(),
  `puntaje_obtenido` float DEFAULT NULL,
  `tiempo_empleado` int(11) DEFAULT NULL,
  `intento_numero` int(11) DEFAULT NULL,
  `progreso_alcanzado` int(11) DEFAULT 0,
  `estado_actual` enum('iniciado','pausado','completado') DEFAULT 'iniciado',
  PRIMARY KEY (`id_progreso`),
  KEY `id_nino` (`id_nino`),
  KEY `id_ejercicio` (`id_ejercicio`),
  CONSTRAINT `1` FOREIGN KEY (`id_nino`) REFERENCES `nino` (`id_nino`) ON DELETE CASCADE,
  CONSTRAINT `2` FOREIGN KEY (`id_ejercicio`) REFERENCES `catalogo_ejercicios` (`id_ejercicio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `progreso_nino`
--

LOCK TABLES `progreso_nino` WRITE;
/*!40000 ALTER TABLE `progreso_nino` DISABLE KEYS */;
/*!40000 ALTER TABLE `progreso_nino` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rol`
--

DROP TABLE IF EXISTS `rol`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol` (
  `id_rol` int(11) NOT NULL,
  `nombre` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rol`
--

LOCK TABLES `rol` WRITE;
/*!40000 ALTER TABLE `rol` DISABLE KEYS */;
INSERT INTO `rol` VALUES (1,'admin'),(2,'tutor'),(3,'nino'),(4,'invitado');
/*!40000 ALTER TABLE `rol` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tutor`
--

DROP TABLE IF EXISTS `tutor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tutor` (
  `id_tut` int(11) NOT NULL AUTO_INCREMENT,
  `id_user` int(11) DEFAULT NULL,
  `nombre` varchar(100) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `celular` varchar(15) DEFAULT NULL,
  `ocupacion` varchar(100) DEFAULT NULL,
  `zona` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id_tut`),
  UNIQUE KEY `id_user` (`id_user`),
  CONSTRAINT `1` FOREIGN KEY (`id_user`) REFERENCES `usuario` (`id_user`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tutor`
--

LOCK TABLES `tutor` WRITE;
/*!40000 ALTER TABLE `tutor` DISABLE KEYS */;
/*!40000 ALTER TABLE `tutor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `id_user` int(11) NOT NULL AUTO_INCREMENT,
  `usr` varchar(50) NOT NULL,
  `psw` varchar(255) NOT NULL,
  `id_rol` int(11) DEFAULT NULL,
  `estado` enum('activo','inactivo') DEFAULT 'activo',
  `fecha_reg` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_user`),
  UNIQUE KEY `usr` (`usr`),
  KEY `id_rol` (`id_rol`),
  CONSTRAINT `1` FOREIGN KEY (`id_rol`) REFERENCES `rol` (`id_rol`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'sis_expert_bd'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-04-19 22:21:42
