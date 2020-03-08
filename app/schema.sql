drop table if exists UserConfig;
create table UserConfig (
       id integer primary key autoincrement,
       VarName text not null,
       VarVal text not null)

