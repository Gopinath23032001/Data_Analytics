INSERT INTO dim_state (state_name, region, is_ut) VALUES
-- Northern
('Jammu and Kashmir', 'Northern', TRUE),
('Ladakh', 'Northern', TRUE),
('Himachal Pradesh', 'Northern', FALSE),
('Punjab', 'Northern', FALSE),
('Haryana', 'Northern', FALSE),
('Delhi', 'Northern', TRUE),
('Uttarakhand', 'Northern', FALSE),
('Uttar Pradesh', 'Northern', FALSE),
('Chandigarh', 'Northern', TRUE),
-- Western
('Rajasthan', 'Western', FALSE),
('Gujarat', 'Western', FALSE),
('Maharashtra', 'Western', FALSE),
('Goa', 'Western', FALSE),
('Dadra and Nagar Haveli and Daman and Diu', 'Western', TRUE),
-- Southern
('Karnataka', 'Southern', FALSE),
('Kerala', 'Southern', FALSE),
('Tamil Nadu', 'Southern', FALSE),
('Andhra Pradesh', 'Southern', FALSE),
('Telangana', 'Southern', FALSE),
('Puducherry', 'Southern', TRUE),
('Lakshadweep', 'Southern', TRUE),
('Andaman and Nicobar Islands', 'Southern', TRUE),
-- Eastern
('West Bengal', 'Eastern', FALSE),
('Odisha', 'Eastern', FALSE),
('Bihar', 'Eastern', FALSE),
('Jharkhand', 'Eastern', FALSE),
-- Central
('Madhya Pradesh', 'Central', FALSE),
('Chhattisgarh', 'Central', FALSE),
-- North-Eastern
('Assam', 'NorthEastern', FALSE),
('Arunachal Pradesh', 'NorthEastern', FALSE),
('Manipur', 'NorthEastern', FALSE),
('Meghalaya', 'NorthEastern', FALSE),
('Mizoram', 'NorthEastern', FALSE),
('Nagaland', 'NorthEastern', FALSE),
('Sikkim', 'NorthEastern', FALSE),
('Tripura', 'NorthEastern', FALSE)
ON CONFLICT (state_name) DO NOTHING;


SELECT * FROM dim_state