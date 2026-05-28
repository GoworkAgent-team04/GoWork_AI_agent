class JobPosting {
  final String id;
  final String title;
  final String? company;
  final String? location;
  final String? salary;
  final String? workType;
  final String? schedule;
  final String? deadline;
  final String? sourceUrl;
  final String? physicalLevel;
  final bool? seniorTag;
  final int? ageMin;
  final int? ageMax;

  JobPosting({
    required this.id,
    required this.title,
    this.company,
    this.location,
    this.salary,
    this.workType,
    this.schedule,
    this.deadline,
    this.sourceUrl,
    this.physicalLevel,
    this.seniorTag,
    this.ageMin,
    this.ageMax,
  });

  factory JobPosting.fromJson(Map<String, dynamic> json) {
    return JobPosting(
      id: json['id'].toString(),
      title: json['title'] ?? '',
      company: json['company'],
      location: json['location'],
      salary: json['salary'],
      workType: json['work_type'],
      schedule: json['schedule'],
      deadline: json['deadline'],
      sourceUrl: json['source_url'],
      physicalLevel: json['physical_level'],
      seniorTag: json['senior_tag'],
      ageMin: json['age_min'],
      ageMax: json['age_max'],
    );
  }
}