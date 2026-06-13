-- Run against nta_portal to replace missing seeded course image filenames with the shared SVG placeholder.
UPDATE courses
SET image_url = '/images/course-placeholder.svg'
WHERE image_url IN ('course2.jpg', 'python_ds.jpg',
                    'images/course2.jpg', 'images/python_ds.jpg',
                    '/images/course2.jpg', '/images/python_ds.jpg')
   OR image_url IS NULL
   OR image_url = '';
