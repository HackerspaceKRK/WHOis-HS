module Whois
  ROOT = Dir.pwd

  def self.root 
    ROOT
  end

  def self.env
    if !!ENV['RACK_ENV']
      'developent'
    end
    return ENV['RACK_ENV']
  end
  
  def self.db_url
    if env == 'production'
      return "sqlite://#{Whois.root}/db/database.sqlite"
    end
    return "sqlite::memory:"
  end
end
