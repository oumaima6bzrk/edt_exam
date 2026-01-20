
-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jan 07, 2026 at 12:54 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `edt_exam`
--

-- --------------------------------------------------------

--
-- Table structure for table `departements`
--

CREATE TABLE `departements` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `departements`
--

INSERT INTO `departements` (`id`, `nom`) VALUES
(1, 'Informatique'),
(2, 'Mathématiques'),
(3, 'Physique'),
(4, 'Électronique');

-- --------------------------------------------------------

--
-- Table structure for table `etudiants`
--

CREATE TABLE `etudiants` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `groupe_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `etudiants`
--

INSERT INTO `etudiants` (`id`, `user_id`, `groupe_id`) VALUES
(1, 1, 1),
(2, 2, 1),
(3, 3, 2),
(4, 4, 3),
(5, 5, 4);

-- --------------------------------------------------------

--
-- Table structure for table `examens`
--

CREATE TABLE `examens` (
  `id` int(11) NOT NULL,
  `module_id` int(11) NOT NULL,
  `formation_id` int(11) NOT NULL,
  `date_examen` date NOT NULL,
  `heure_debut` time NOT NULL,
  `duree_minutes` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `examens_groupes_salles`
--

CREATE TABLE `examens_groupes_salles` (
  `id` int(11) NOT NULL,
  `examen_id` int(11) NOT NULL,
  `groupe_id` int(11) NOT NULL,
  `salle_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `formations`
--

CREATE TABLE `formations` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `departement_id` int(11) NOT NULL,
  `niveau_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `formations`
--

INSERT INTO `formations` (`id`, `nom`, `departement_id`, `niveau_id`) VALUES
(1, 'Informatique L1', 1, 1),
(2, 'Informatique L2', 1, 2),
(3, 'Mathématiques L1', 2, 1),
(4, 'Physique L1', 3, 1);

-- --------------------------------------------------------

--
-- Table structure for table `groupes`
--

CREATE TABLE `groupes` (
  `id` int(11) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `formation_id` int(11) NOT NULL,
  `effectif` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `groupes`
--

INSERT INTO `groupes` (`id`, `nom`, `formation_id`, `effectif`) VALUES
(1, 'G1', 1, 30),
(2, 'G2', 1, 30),
(3, 'G1', 2, 28),
(4, 'G1', 3, 35);

-- --------------------------------------------------------

--
-- Table structure for table `modules`
--

CREATE TABLE `modules` (
  `id` int(11) NOT NULL,
  `nom` varchar(100) NOT NULL,
  `formation_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `niveaux`
--

CREATE TABLE `niveaux` (
  `id` int(11) NOT NULL,
  `code` varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `niveaux`
--

INSERT INTO `niveaux` (`id`, `code`) VALUES
(1, 'L1'),
(2, 'L2'),
(3, 'L3'),
(4, 'M1'),
(5, 'M2');

-- --------------------------------------------------------

--
-- Table structure for table `professeurs`
--

CREATE TABLE `professeurs` (
  `id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `departement_id` int(11) NOT NULL,
  `specialite` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `salles`
--

CREATE TABLE `salles` (
  `id` int(11) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `capacite` int(11) NOT NULL,
  `type` enum('SALLE','AMPHI') NOT NULL,
  `batiment` varchar(50) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `salles`
--

INSERT INTO `salles` (`id`, `nom`, `capacite`, `type`, `batiment`) VALUES
(1, 'Salle 101', 40, 'SALLE', NULL),
(2, 'Salle 102', 30, 'SALLE', NULL),
(3, 'Amphi A', 200, 'SALLE', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `surveillances`
--

CREATE TABLE `surveillances` (
  `id` int(11) NOT NULL,
  `examen_id` int(11) NOT NULL,
  `salle_id` int(11) NOT NULL,
  `prof_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('ADMIN_EXAM','VICE_DOYEN','CHEF_DEPT','PROF','ETUDIANT') NOT NULL,
  `is_active` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `email`, `password`, `role`, `is_active`) VALUES
(1, 'ali@mail.com', '1234', 'ETUDIANT', 1),
(2, 'sara@mail.com', '1234', 'ETUDIANT', 1),
(3, 'karim@mail.com', '1234', 'ETUDIANT', 1),
(4, 'lina@mail.com', '1234', 'ETUDIANT', 1),
(5, 'yacine@mail.com', '1234', 'ETUDIANT', 1);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `departements`
--
ALTER TABLE `departements`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `etudiants`
--
ALTER TABLE `etudiants`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`),
  ADD KEY `groupe_id` (`groupe_id`);

--
-- Indexes for table `examens`
--
ALTER TABLE `examens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `module_id` (`module_id`),
  ADD KEY `formation_id` (`formation_id`);

--
-- Indexes for table `examens_groupes_salles`
--
ALTER TABLE `examens_groupes_salles`
  ADD PRIMARY KEY (`id`),
  ADD KEY `examen_id` (`examen_id`),
  ADD KEY `groupe_id` (`groupe_id`),
  ADD KEY `salle_id` (`salle_id`);

--
-- Indexes for table `formations`
--
ALTER TABLE `formations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `departement_id` (`departement_id`),
  ADD KEY `niveau_id` (`niveau_id`);

--
-- Indexes for table `groupes`
--
ALTER TABLE `groupes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `formation_id` (`formation_id`);

--
-- Indexes for table `modules`
--
ALTER TABLE `modules`
  ADD PRIMARY KEY (`id`),
  ADD KEY `formation_id` (`formation_id`);

--
-- Indexes for table `niveaux`
--
ALTER TABLE `niveaux`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `code` (`code`);

--
-- Indexes for table `professeurs`
--
ALTER TABLE `professeurs`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`),
  ADD KEY `departement_id` (`departement_id`);

--
-- Indexes for table `salles`
--
ALTER TABLE `salles`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `surveillances`
--
ALTER TABLE `surveillances`
  ADD PRIMARY KEY (`id`),
  ADD KEY `examen_id` (`examen_id`),
  ADD KEY `salle_id` (`salle_id`),
  ADD KEY `prof_id` (`prof_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `departements`
--
ALTER TABLE `departements`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `etudiants`
--
ALTER TABLE `etudiants`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `examens`
--
ALTER TABLE `examens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `examens_groupes_salles`
--
ALTER TABLE `examens_groupes_salles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `formations`
--
ALTER TABLE `formations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `groupes`
--
ALTER TABLE `groupes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `modules`
--
ALTER TABLE `modules`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `niveaux`
--
ALTER TABLE `niveaux`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `professeurs`
--
ALTER TABLE `professeurs`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `salles`
--
ALTER TABLE `salles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `surveillances`
--
ALTER TABLE `surveillances`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `etudiants`
--
ALTER TABLE `etudiants`
  ADD CONSTRAINT `etudiants_ibfk_1` FOREIGN KEY (`groupe_id`) REFERENCES `groupes` (`id`);

--
-- Constraints for table `examens`
--
ALTER TABLE `examens`
  ADD CONSTRAINT `examens_ibfk_1` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`),
  ADD CONSTRAINT `examens_ibfk_2` FOREIGN KEY (`formation_id`) REFERENCES `formations` (`id`);

--
-- Constraints for table `examens_groupes_salles`
--
ALTER TABLE `examens_groupes_salles`
  ADD CONSTRAINT `examens_groupes_salles_ibfk_1` FOREIGN KEY (`examen_id`) REFERENCES `examens` (`id`),
  ADD CONSTRAINT `examens_groupes_salles_ibfk_2` FOREIGN KEY (`groupe_id`) REFERENCES `groupes` (`id`),
  ADD CONSTRAINT `examens_groupes_salles_ibfk_3` FOREIGN KEY (`salle_id`) REFERENCES `salles` (`id`);

--
-- Constraints for table `formations`
--
ALTER TABLE `formations`
  ADD CONSTRAINT `formations_ibfk_1` FOREIGN KEY (`departement_id`) REFERENCES `departements` (`id`),
  ADD CONSTRAINT `formations_ibfk_2` FOREIGN KEY (`niveau_id`) REFERENCES `niveaux` (`id`);

--
-- Constraints for table `groupes`
--
ALTER TABLE `groupes`
  ADD CONSTRAINT `groupes_ibfk_1` FOREIGN KEY (`formation_id`) REFERENCES `formations` (`id`);

--
-- Constraints for table `modules`
--
ALTER TABLE `modules`
  ADD CONSTRAINT `modules_ibfk_1` FOREIGN KEY (`formation_id`) REFERENCES `formations` (`id`);

--
-- Constraints for table `professeurs`
--
ALTER TABLE `professeurs`
  ADD CONSTRAINT `professeurs_ibfk_1` FOREIGN KEY (`departement_id`) REFERENCES `departements` (`id`);

--
-- Constraints for table `surveillances`
--
ALTER TABLE `surveillances`
  ADD CONSTRAINT `surveillances_ibfk_1` FOREIGN KEY (`examen_id`) REFERENCES `examens` (`id`),
  ADD CONSTRAINT `surveillances_ibfk_2` FOREIGN KEY (`salle_id`) REFERENCES `salles` (`id`),
  ADD CONSTRAINT `surveillances_ibfk_3` FOREIGN KEY (`prof_id`) REFERENCES `professeurs` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
