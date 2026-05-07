/* change the password if used on remote servers */
CREATE USER `protos`@`%` IDENTIFIED BY 'protos';

GRANT Select ON TABLE `player`.`item_proto` TO `protos`@`%`;

GRANT Select ON TABLE `player`.`mob_proto` TO `protos`@`%`;
