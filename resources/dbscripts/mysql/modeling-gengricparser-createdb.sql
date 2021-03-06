--
-- Copyright 2018 ZTE Corporation.
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.
--

/******************create database and user***************************/
use mysql;

create database if not exists genericparser CHARACTER SET utf8;


GRANT ALL PRIVILEGES ON genericparser.* TO 'genericparser'@'%' IDENTIFIED BY 'genericparser' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON mysql.* TO 'genericparser'@'%' IDENTIFIED BY 'genericparser' WITH GRANT OPTION;

GRANT ALL PRIVILEGES ON genericparser.* TO 'genericparser'@'localhost' IDENTIFIED BY 'genericparser' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON mysql.* TO 'genericparser'@'localhost' IDENTIFIED BY 'genericparser' WITH GRANT OPTION;
FLUSH PRIVILEGES;
