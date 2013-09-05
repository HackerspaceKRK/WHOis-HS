require 'spec_helper'

describe User do

  it { should respond_to :display_name }
  it { should validate_length_of(:display_name).length(100) }
  it { should validate_presence_of(:display_name) }

  it { should respond_to :login }
  it { should validate_presence_of(:login) }
  it { should validate_length_of(:login).max(10) }

  it { should respond_to :id }


  it { should respond_to :last_login }

  it { should respond_to :password= }

  it { should respond_to :authenticate }

  let(:user){ User.new }

  it "hash passwords" do
    password = 'ala ma kota'
    hash = Digest::SHA2.hexdigest(password)
    user.password = password
    user.password.should be == hash
  end


  it "authorized same password as was set" do
    user.password = 'ala ma kota'
    user.authenticate('ala ma kota').should be_true
  end
end
