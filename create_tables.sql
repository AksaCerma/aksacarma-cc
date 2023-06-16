CREATE TABLE `user` (
 `id` int NOT NULL AUTO_INCREMENT,
 `username` varchar(50) NOT NULL,
 `pass_hash` text NOT NULL,
 `name` varchar(50) NOT NULL,
 `avatar_url` text NOT NULL,
 PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=29 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `history` (
 `id` int NOT NULL AUTO_INCREMENT,
 `user_id` int NOT NULL,
 `prediction` text NOT NULL,
 `image_url` text NOT NULL,
 `datetime` datetime NOT NULL,
 PRIMARY KEY (`id`),
 KEY `user_id` (`user_id`),
 KEY `user_id_2` (`user_id`),
 CONSTRAINT `history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=141 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `search_result` (
 `history_id` int NOT NULL,
 `title` text NOT NULL,
 `url` text NOT NULL,
 `description` text NOT NULL,
 `image_url` text,
 KEY `history_id` (`history_id`),
 CONSTRAINT `search_result_ibfk_1` FOREIGN KEY (`history_id`) REFERENCES `history` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
