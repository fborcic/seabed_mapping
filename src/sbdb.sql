CREATE TABLE sessions(
	_id          INTEGER PRIMARY KEY, 
	starttime    TIMESTAMP, 
	stoptime     TIMESTAMP);
	
CREATE TABLE positions(
	_id          INTEGER PRIMARY KEY,
	passing_time TIMESTAMP,
	lat          TEXT,
	lon          TEXT,
	speed        REAL,
	heading      REAL,
	time_between REAL,
	depth        REAL,
	session_id   INTEGER,
	FOREIGN KEY(session_id) REFERENCES sessions(_id));
	
CREATE TABLE points(
	_id          INTEGER PRIMARY KEY,
	x            REAL,
	y            REAL,
	z            REAL,
	position_id  INTEGER,
	origin_id    INTEGER,
	session_id   INTEGER,
	FOREIGN KEY(position_id) REFERENCES positions(_id)
	FOREIGN KEY(origin_id)   REFERENCES origins(_id),
	FOREIGN KEY(session_id) REFERENCES sessions(_id));

CREATE TABLE origins(
	_id          INTEGER PRIMARY KEY,
	x            REAL,
	y            REAL);

CREATE TABLE triangles(
	_id          INTEGER PRIMARY KEY,
	v1_id        INTEGER	NOT NULL,
	v2_id        INTEGER	NOT NULL,
	v3_id        INTEGER	NOT NULL,
	FOREIGN KEY(v1_id) REFERENCES points(_id),
	FOREIGN KEY(v2_id) REFERENCES points(_id),
	FOREIGN KEY(v3_id) REFERENCES points(_id));