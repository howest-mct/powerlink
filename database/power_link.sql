CREATE DATABASE  IF NOT EXISTS `power_link` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `power_link`;
-- MySQL dump 10.13  Distrib 8.0.38, for Win64 (x86_64)
--
-- Host: localhost    Database: power_link
-- ------------------------------------------------------
-- Server version	5.5.5-10.11.11-MariaDB-0+deb12u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `actuators`
--

DROP TABLE IF EXISTS `actuators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `actuators` (
  `actuator_id` int(11) NOT NULL AUTO_INCREMENT,
  `actuator_name` varchar(100) NOT NULL,
  PRIMARY KEY (`actuator_id`),
  UNIQUE KEY `actuator_name_UNIQUE` (`actuator_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `actuators`
--

LOCK TABLES `actuators` WRITE;
/*!40000 ALTER TABLE `actuators` DISABLE KEYS */;
/*!40000 ALTER TABLE `actuators` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inhabitants`
--

DROP TABLE IF EXISTS `inhabitants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inhabitants` (
  `inhabitant_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(45) NOT NULL,
  `last_name` varchar(45) DEFAULT NULL,
  `badge_id` varchar(100) NOT NULL,
  PRIMARY KEY (`inhabitant_id`),
  UNIQUE KEY `badge_id_UNIQUE` (`badge_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inhabitants`
--

LOCK TABLES `inhabitants` WRITE;
/*!40000 ALTER TABLE `inhabitants` DISABLE KEYS */;
/*!40000 ALTER TABLE `inhabitants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inputs`
--

DROP TABLE IF EXISTS `inputs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inputs` (
  `input_id` int(11) NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `value` float NOT NULL,
  `value_unit` varchar(10) DEFAULT NULL,
  `user_input_id` int(11) NOT NULL,
  PRIMARY KEY (`input_id`),
  KEY `fk2_user_input_id_idx` (`user_input_id`),
  CONSTRAINT `fk2_user_input_id` FOREIGN KEY (`user_input_id`) REFERENCES `user_inputs` (`user_input_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inputs`
--

LOCK TABLES `inputs` WRITE;
/*!40000 ALTER TABLE `inputs` DISABLE KEYS */;
/*!40000 ALTER TABLE `inputs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `measurements`
--

DROP TABLE IF EXISTS `measurements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `measurements` (
  `measurement_id` int(11) NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `value` float NOT NULL,
  `value_unit` varchar(10) DEFAULT NULL,
  `sensor_id` int(11) NOT NULL,
  PRIMARY KEY (`measurement_id`),
  KEY `fk1_sensor_id_idx` (`sensor_id`),
  CONSTRAINT `fk1_sensor_id` FOREIGN KEY (`sensor_id`) REFERENCES `sensors` (`sensor_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `measurements`
--

LOCK TABLES `measurements` WRITE;
/*!40000 ALTER TABLE `measurements` DISABLE KEYS */;
/*!40000 ALTER TABLE `measurements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sensors`
--

DROP TABLE IF EXISTS `sensors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sensors` (
  `sensor_id` int(11) NOT NULL AUTO_INCREMENT,
  `sensor_name` varchar(100) NOT NULL,
  PRIMARY KEY (`sensor_id`),
  UNIQUE KEY `sensor_name_UNIQUE` (`sensor_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sensors`
--

LOCK TABLES `sensors` WRITE;
/*!40000 ALTER TABLE `sensors` DISABLE KEYS */;
/*!40000 ALTER TABLE `sensors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `signals`
--

DROP TABLE IF EXISTS `signals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `signals` (
  `signal_id` int(11) NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL,
  `value` float NOT NULL,
  `value_unit` varchar(10) DEFAULT NULL,
  `actuator_id` int(11) NOT NULL,
  PRIMARY KEY (`signal_id`),
  KEY `fk3_actuator_id_idx` (`actuator_id`),
  CONSTRAINT `fk3_actuator_id` FOREIGN KEY (`actuator_id`) REFERENCES `actuators` (`actuator_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `signals`
--

LOCK TABLES `signals` WRITE;
/*!40000 ALTER TABLE `signals` DISABLE KEYS */;
/*!40000 ALTER TABLE `signals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_inputs`
--

DROP TABLE IF EXISTS `user_inputs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_inputs` (
  `user_input_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_input_name` varchar(100) NOT NULL,
  PRIMARY KEY (`user_input_id`),
  UNIQUE KEY `user_input_name_UNIQUE` (`user_input_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_inputs`
--

LOCK TABLES `user_inputs` WRITE;
/*!40000 ALTER TABLE `user_inputs` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_inputs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'power_link'
--

--
-- Dumping routines for database 'power_link'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-05-26 14:20:07
