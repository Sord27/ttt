#!/usr/bin/env ruby

require 'json'

REPLACE_ME = "xxxxx"

file = File.read('config.json')
data_hash = JSON.parse(file)
data_hash.each do |key, value|
  value['backoffice']['username'] = REPLACE_ME
  value['backoffice']['password'] = REPLACE_ME
  value['sql']['ssh_username'] = REPLACE_ME
  if key == "prod" or key == "stage" then
    value['sql']['sql_password'] = REPLACE_ME
  end
end

File.rename('config.json', 'config_backup.json')

output = File.new('config.json', 'w')
output.write(JSON.pretty_generate(data_hash))
