from flask import Flask
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with
import pymongo

app = Flask(__name__)
api = Api(app)
client = pymongo.MongoClient('mongodb+srv://prodigal_be_test_01:prodigaltech@test-01-ateon.mongodb.net/sample_training')
db = client['sample_training']
map_student = {}
student_coll = db['students']
for student in student_coll.find():
	map_student[student['_id']] = student['name']


class Student(Resource):
	def get(self):
		student_coll = db['students']
		output = []
		student_list = []
		for student in student_coll.find():
			if student["_id"] not in student_list:
				output.append({'student_id': student['_id'], 'student_name': student['name']})
				student_list.append(student["_id"])
		return output


class ClassesByStudent(Resource):
	def get(self, student_id):
		grades_coll = db['grades']
		classes = []
		for grade in grades_coll.find({'student_id':student_id}):
			classes.append({"class_id": grade["class_id"]})
		output = {'student_id': student_id, 'student_name': map_student.get(student['name'], None), 'classes': classes}
		return output


class StudentPerformance(Resource):
	@staticmethod
	def get(self, student_id):
		grades_coll = db['grades']
		classes = []
		for grade in grades_coll.find({'student_id': student_id}):
			total_marks = 0
			for score in grade['scores']:
				total_marks += score['score']
			classes.append({"class_id": grade["class_id"], "total_marks": int(total_marks)})

		output = {'student_id': student_id, 'student_name': map_student.get(student['name'], None), 'classes': classes}
		return output


class Classes(Resource):
	@staticmethod
	def get(self):
		grades_coll = db['grades']
		output = []
		id = []
		for grade in grades_coll.find():
			if grade['class_id'] not in id:
				output.append({'class_id': grade['class_id']})
				id.append(grade['class_id'])
		return output


class StudentTakingCourse(Resource):
	@staticmethod
	def get(self, class_id):
		grades_coll = db['grades']
		output = {"class_id": class_id, "students":[]}
		student_list = []
		for grade in grades_coll.find({"class_id": class_id}):
			if grade["student_id"] not in student_list:
				students = {"student_id": grade["student_id"], "student_name": map_student[grade["student_id"]]}
				student_list.append(grade["student_id"])
				output["students"].append(students)
		return output


class PerformanceEachStudent(Resource):
	@staticmethod
	def get(self, class_id):
		grades_coll = db['grades']
		output = {"class_id": class_id, "students": []}
		student_list = []
		for grade in grades_coll.find({'class_id': class_id}):
			total_marks = 0
			for score in grade['scores']:
				total_marks += score['score']

			if grade["student_id"] not in student_list:
				students = {"student_id": grade["student_id"], "student_name": map_student[
					grade["student_id"]], "total_marks": int(total_marks)}
				output["students"].append(students)
				student_list.append(grade["student_id"])
		return output


class GradeSheet(Resource):
	@staticmethod
	def get(self, class_id):
		grades_coll = db['grades']
		students = []

		for grade in grades_coll.find({'class_id': class_id}):
			total_marks = 0
			details = []
			for score in grade['scores']:
				info = {"type": score['type'], "marks": int(score['score'])}
				total_marks += score['score']
				details.append(info)
			info = {"type": "total", "marks": int(total_marks)}
			details.append(info)

			student_info = {"student_id": grade["student_id"], "student_name": map_student[
				grade["student_id"]], "details": details}
			students.append(student_info)
		students = sorted(students, key=lambda i: i["details"][4]['marks'], reverse=True)
		total = len(students)
		top_1_by_12 = int(total/12)
		total -= top_1_by_12
		top_1_by_6 = int(total/6)
		total -= top_1_by_6
		top_1_by_6 += top_1_by_12
		top_1_by_4 = int(total / 4)
		top_1_by_4 += top_1_by_6
		i = 1
		for student in students:
			if i <= top_1_by_12:
				grade = 'A'
			elif i <= top_1_by_6:
				grade = 'B'
			elif i <= top_1_by_4:
				grade = 'C'
			else:
				grade = 'D'
			student['grade'] = grade
			i += 1
		student = {"class_id": class_id, "students": students}
		return student


class StudentInCourse(Resource):
	@staticmethod
	def get(self, class_id, student_id):
		grades_coll = db['grades']
		student_info = {"class_id": class_id, "student_id": student_id, "student_name": None, "marks": None}

		for grade in grades_coll.find({'class_id': class_id, "student_id": student_id}):
			total_marks = 0
			details = []
			for score in grade['scores']:
				info = {"type": score['type'], "marks": int(score['score'])}
				total_marks += score['score']
				details.append(info)
			info = {"type": "total", "marks": int(total_marks)}
			details.append(info)

			student_info = {"class_id": class_id, "student_id": grade["student_id"], "student_name": map_student[
				grade["student_id"]], "marks": details}
		return student_info


api.add_resource(Student, "/students")
api.add_resource(ClassesByStudent, "/student/<int:student_id>/classes", endpoint="classes_by_student")
api.add_resource(StudentPerformance, "/student/<int:student_id>/performance")
api.add_resource(Classes, "/classes")
api.add_resource(StudentTakingCourse, "/class/<int:class_id>/students", endpoint="student_taking_course")
api.add_resource(PerformanceEachStudent, "/class/<int:class_id>/performance", endpoint="performance_by_each_student")
api.add_resource(GradeSheet, "/class/<int:class_id>/final-grade-sheet")
api.add_resource(
	StudentInCourse, "/class/<int:class_id>/student/<int:student_id>", "/student/<int:student_id>/class/<int:class_id>"
	, endpoint='student_in_course')


if __name__ == "__main__":
	app.run(debug=True, port=2020)
