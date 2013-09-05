require 'spec_helper'

describe Device do
  
  it { should respond_to(:mac) }

  it { should validate_format_of(:mac).with(/[0-9A-F]{2}(\:[0-9A-F]{2}){5}/) }

  it { should respond_to(:last_seen) }

  it { should belong_to(:user) }
end
