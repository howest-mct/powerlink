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
-- Table structure for table `component_logs`
--

DROP TABLE IF EXISTS `component_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `component_logs` (
  `log_id` int(11) NOT NULL AUTO_INCREMENT,
  `datetime` datetime NOT NULL DEFAULT current_timestamp(),
  `value` float NOT NULL,
  `component_id` int(11) NOT NULL,
  PRIMARY KEY (`log_id`),
  UNIQUE KEY `history_id_UNIQUE` (`log_id`),
  KEY `fk1_component_id_idx` (`component_id`),
  CONSTRAINT `fk1_component_id` FOREIGN KEY (`component_id`) REFERENCES `components` (`component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `component_logs`
--

LOCK TABLES `component_logs` WRITE;
/*!40000 ALTER TABLE `component_logs` DISABLE KEYS */;
INSERT INTO `component_logs` VALUES (1,'2025-05-01 09:15:23',75,1),(2,'2025-05-02 14:32:45',40,2),(3,'2025-05-03 07:19:08',60,3),(4,'2025-05-04 22:41:56',30,4),(5,'2025-05-05 11:05:34',20,5),(6,'2025-05-06 03:27:19',1,6),(7,'2025-05-07 16:53:42',0,7),(8,'2025-05-08 19:12:07',1,8),(9,'2025-05-09 04:38:51',1,9),(10,'2025-05-10 13:46:29',0,10),(11,'2025-05-11 08:09:14',50,11),(12,'2025-05-12 15:22:33',80,12),(13,'2025-05-13 06:47:55',0.18,13),(14,'2025-05-14 23:04:16',0.09,14),(15,'2025-05-15 10:29:38',1.9,15),(16,'2025-05-16 02:51:47',0.6,16),(17,'2025-05-17 17:13:25',1.2,17),(18,'2025-05-18 20:36:09',0.9,18),(19,'2025-05-19 05:58:43',65,1),(20,'2025-05-20 12:21:04',55,2),(21,'2025-05-21 07:43:26',45,3),(22,'2025-05-22 14:06:48',70,4),(23,'2025-05-23 01:28:57',15,5),(24,'2025-05-24 18:51:19',0,6),(25,'2025-05-25 09:14:41',1,7),(26,'2025-05-26 03:37:02',0,8),(27,'2025-05-27 11:59:24',1,9),(28,'2025-05-01 21:22:46',0,10),(29,'2025-05-02 06:45:08',60,11),(30,'2025-05-03 13:07:29',25,12),(31,'2025-05-04 08:29:51',0.24,13),(32,'2025-05-05 15:52:13',0.15,14),(33,'2025-05-06 23:14:35',2.2,15),(34,'2025-05-07 04:36:57',0.4,16),(35,'2025-05-08 11:59:19',1.5,17),(36,'2025-05-09 02:21:41',1,18),(37,'2025-05-10 17:44:02',80,1),(38,'2025-05-11 20:06:24',35,2),(39,'2025-05-12 05:28:46',50,3),(40,'2025-05-13 12:51:08',25,4),(41,'2025-05-14 07:13:29',10,5),(42,'2025-05-15 14:35:51',1,6),(43,'2025-05-16 01:58:13',0,7),(44,'2025-05-17 19:20:35',0,8),(45,'2025-05-18 09:42:57',1,9),(46,'2025-05-19 03:05:19',1,10),(47,'2025-05-20 16:27:41',70,11),(48,'2025-05-21 22:50:02',90,12),(49,'2025-05-22 06:12:24',0.12,13),(50,'2025-05-23 13:34:46',0.21,14),(51,'2025-05-24 08:57:08',1.3,15),(52,'2025-05-25 15:19:29',0.8,16),(53,'2025-05-26 01:41:51',0.9,17),(54,'2025-05-27 09:04:13',1.4,18),(55,'2025-05-01 14:26:35',55,1),(56,'2025-05-02 21:48:57',60,2),(57,'2025-05-03 07:11:19',40,3),(58,'2025-05-04 14:33:41',65,4),(59,'2025-05-05 02:56:02',30,5),(60,'2025-05-06 09:18:24',0,6),(61,'2025-05-07 16:40:46',1,7),(62,'2025-05-08 23:03:08',0,8),(63,'2025-05-09 05:25:29',1,9),(64,'2025-05-10 12:47:51',0,10),(65,'2025-05-11 19:10:13',45,11),(66,'2025-05-12 01:32:35',70,12),(67,'2025-05-13 08:54:57',0.27,13),(68,'2025-05-14 15:17:19',0.06,14),(69,'2025-05-15 22:39:41',1.7,15),(70,'2025-05-16 05:02:02',0.5,16),(71,'2025-05-17 12:24:24',1.1,17),(72,'2025-05-18 18:46:46',0.7,18),(73,'2025-05-19 01:09:08',70,1),(74,'2025-05-20 08:31:29',45,2),(75,'2025-05-21 14:53:51',55,3),(76,'2025-05-22 21:16:13',20,4),(77,'2025-05-23 03:38:35',25,5),(78,'2025-05-24 10:00:57',0,6),(79,'2025-05-25 16:23:19',1,7),(80,'2025-05-26 22:45:41',0,8),(81,'2025-05-27 05:08:02',1,9),(82,'2025-05-01 11:30:24',0,10),(83,'2025-05-02 17:52:46',65,11),(84,'2025-05-03 00:15:08',35,12),(85,'2025-05-04 06:37:29',0.15,13),(86,'2025-05-05 13:59:51',0.18,14),(87,'2025-05-06 20:22:13',2,15),(88,'2025-05-07 02:44:35',0.9,16),(89,'2025-05-08 09:06:57',1.8,17),(90,'2025-05-09 15:29:19',1.2,18),(91,'2025-05-10 21:51:41',60,1),(92,'2025-05-11 04:14:02',50,2),(93,'2025-05-12 10:36:24',70,3),(94,'2025-05-13 16:58:46',40,4),(95,'2025-05-14 23:21:08',15,5),(96,'2025-05-15 05:43:29',1,6),(97,'2025-05-16 12:05:51',0,7),(98,'2025-05-17 18:28:13',1,8),(99,'2025-05-18 00:50:35',0,9),(100,'2025-05-19 07:12:57',0,10);
/*!40000 ALTER TABLE `component_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `components`
--

DROP TABLE IF EXISTS `components`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `components` (
  `component_id` int(11) NOT NULL AUTO_INCREMENT,
  `component_name` varchar(45) NOT NULL,
  `value_unit` varchar(45) NOT NULL,
  PRIMARY KEY (`component_id`),
  UNIQUE KEY `component_name_UNIQUE` (`component_name`),
  UNIQUE KEY `component_id_UNIQUE` (`component_id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `components`
--

LOCK TABLES `components` WRITE;
/*!40000 ALTER TABLE `components` DISABLE KEYS */;
INSERT INTO `components` VALUES (1,'heater','power %'),(2,'airco','speed %'),(3,'led_bottom','brightness %'),(4,'led_top','brightness %'),(5,'led_outdoors','brightness %'),(6,'solenoid_lock','locked/unlocked'),(7,'motion_sensor','moten detected'),(8,'button_lights','off/on'),(9,'reed_switch','closed/open'),(10,'rfid','no access/access'),(11,'temp_sensor','temperature range %'),(12,'light_sensor','light intensity range %'),(13,'wh_lighting_lower','wh'),(14,'wh_lighting_upper','wh'),(15,'wh_heater','wh'),(16,'wh_airco','wh'),(17,'wh_in_battery','wh'),(18,'wh_out_battery','wh');
/*!40000 ALTER TABLE `components` ENABLE KEYS */;
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
  `card_id` varchar(45) NOT NULL,
  PRIMARY KEY (`inhabitant_id`),
  UNIQUE KEY `badge_id_UNIQUE` (`card_id`),
  UNIQUE KEY `inhabitant_id_UNIQUE` (`inhabitant_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inhabitants`
--

LOCK TABLES `inhabitants` WRITE;
/*!40000 ALTER TABLE `inhabitants` DISABLE KEYS */;
INSERT INTO `inhabitants` VALUES (1,'Bart','Gekiere','246629489228'),(2,'Els','Verhelst','462700356070');
/*!40000 ALTER TABLE `inhabitants` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schedule_types`
--

DROP TABLE IF EXISTS `schedule_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schedule_types` (
  `type_id` int(11) NOT NULL AUTO_INCREMENT,
  `type_name` varchar(45) NOT NULL,
  PRIMARY KEY (`type_id`),
  UNIQUE KEY `type_id_UNIQUE` (`type_id`),
  UNIQUE KEY `type_name_UNIQUE` (`type_name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schedule_types`
--

LOCK TABLES `schedule_types` WRITE;
/*!40000 ALTER TABLE `schedule_types` DISABLE KEYS */;
INSERT INTO `schedule_types` VALUES (1,'climate_schedule'),(2,'lighting_schedule');
/*!40000 ALTER TABLE `schedule_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schedules`
--

DROP TABLE IF EXISTS `schedules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schedules` (
  `schedule_id` int(11) NOT NULL AUTO_INCREMENT,
  `schedule_name` varchar(45) NOT NULL,
  `start_time` varchar(5) NOT NULL,
  `end_time` varchar(5) NOT NULL,
  `value` float NOT NULL DEFAULT 0,
  `value_unit` varchar(45) NOT NULL,
  `enabled` tinyint(4) NOT NULL DEFAULT 0,
  `type_id` int(11) NOT NULL,
  `component_id` int(11) NOT NULL,
  PRIMARY KEY (`schedule_id`),
  UNIQUE KEY `schedule_id_UNIQUE` (`schedule_id`),
  KEY `fk2_component_id_idx` (`component_id`),
  KEY `fk3_type_id_idx` (`type_id`),
  CONSTRAINT `fk2_component_id` FOREIGN KEY (`component_id`) REFERENCES `components` (`component_id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `fk3_type_id` FOREIGN KEY (`type_id`) REFERENCES `schedule_types` (`type_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schedules`
--

LOCK TABLES `schedules` WRITE;
/*!40000 ALTER TABLE `schedules` DISABLE KEYS */;
INSERT INTO `schedules` VALUES (1,'heater_schedule','07:00','21:00',26,'temperature degrees',0,1,1),(2,'airco_schedule','06:00','22:00',21,'temperature degrees',0,1,2),(3,'lighting_lower_schedule','22:00','06:00',50,'brightness %',0,2,3),(4,'lighting_upper_schedule','22:00','06:00',50,'brightness %',0,2,4);
/*!40000 ALTER TABLE `schedules` ENABLE KEYS */;
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

-- Dump completed on 2025-05-30 18:28:36
