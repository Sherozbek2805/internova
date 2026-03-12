-- SQLite
-- SQLite
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT,

name TEXT NOT NULL,

email TEXT UNIQUE NOT NULL,

password TEXT NOT NULL,

role TEXT NOT NULL CHECK(role IN ('student','company','admin')),

school TEXT,

skills TEXT,

banned INTEGER DEFAULT 0,

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE companies (

id INTEGER PRIMARY KEY AUTOINCREMENT,

user_id INTEGER NOT NULL,

name TEXT NOT NULL,

description TEXT,

website TEXT,

verified INTEGER DEFAULT 0,

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE internships (

id INTEGER PRIMARY KEY AUTOINCREMENT,

title TEXT NOT NULL,

description TEXT,

company_id INTEGER NOT NULL,

location TEXT,

duration TEXT,

paid INTEGER DEFAULT 0,

deadline TEXT,

approved INTEGER DEFAULT 0,

views INTEGER DEFAULT 0,

applications_count INTEGER DEFAULT 0,

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(company_id) REFERENCES companies(id)
);

CREATE TABLE applications (

id INTEGER PRIMARY KEY AUTOINCREMENT,

student_id INTEGER NOT NULL,

internship_id INTEGER NOT NULL,

status TEXT DEFAULT 'pending',

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(student_id) REFERENCES users(id),

FOREIGN KEY(internship_id) REFERENCES internships(id),

UNIQUE(student_id, internship_id)
);

CREATE TABLE analytics (

id INTEGER PRIMARY KEY AUTOINCREMENT,

internship_id INTEGER UNIQUE,

views INTEGER DEFAULT 0,

applications INTEGER DEFAULT 0,

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

FOREIGN KEY(internship_id) REFERENCES internships(id)
);

