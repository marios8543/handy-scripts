from requests import get
from pymysql import connect
import os
from zipfile import ZipFile
from io import BytesIO

res = get("https://www.ip2location.com/download?token={}&file=DB3LITE".format(os.getenv("token")))
conn = connect(host=getenv("db_host"),user=os.getenv("db_user"),password=os.getenv("db_pass"),db=getenv("db_db"),local_infile=True)
db = conn.cursor()
file = BytesIO()

db.execute("""
CREATE TABLE IF NOT EXISTS `ip2location_db3`(
	`ip_from` INT(10) UNSIGNED,
	`ip_to` INT(10) UNSIGNED,
	`country_code` CHAR(2),
	`country_name` VARCHAR(64),
	`region_name` VARCHAR(128),
	`city_name` VARCHAR(128),
	INDEX `idx_ip_from` (`ip_from`),
	INDEX `idx_ip_to` (`ip_to`),
	INDEX `idx_ip_from_to` (`ip_from`, `ip_to`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
""")

if res.ok:
    file.write(res.content)
    with ZipFile(file) as zip:
        zip.extract("IP2LOCATION-LITE-DB3.CSV")
        db.execute("TRUNCATE TABLE `ip2location_db3`")
        db.execute("""
            LOAD DATA LOCAL
	           INFILE '{}/IP2LOCATION-LITE-DB3.CSV'
            INTO TABLE
	           `ip2location_db3`
            FIELDS TERMINATED BY ','
            ENCLOSED BY '"'
            LINES TERMINATED BY '\r\n'
            IGNORE 0 LINES;
        """.format(os.path.dirname(os.path.realpath(__file__))))
else:
    print("Could not download. ({}) ({})".format(res.status_code,res.content))
