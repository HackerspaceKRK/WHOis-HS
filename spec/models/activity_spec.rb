require 'spec_helper'

describe Activity do
  it { should respond_to(:form) }
  it { should respond_to(:to) }

  it { should belong_to(:user) }
end
