require 'data_mapper'
DataMapper.setup(:default,Whois.db_url)

Dir.chdir('app') do
  Dir['models/**.rb'].each do |model| 
    require_relative model
  end
end

DataMapper.finalize
DataMapper.auto_upgrade!


