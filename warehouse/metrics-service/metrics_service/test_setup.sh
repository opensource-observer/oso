apt-get install -y tmux vim git

cd /usr/src
mv app old
git clone https://github.com/opensource-observer/oso.git
mv oso app
cd app
git checkout ravenac95/test-duckdb-cluster