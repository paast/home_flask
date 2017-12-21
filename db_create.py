from main import db, User, Node, Link


def run():
	db.create_all()

if __name__ == "__main__":
	run()