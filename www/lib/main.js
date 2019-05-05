$(document).ready(function(){
    M.AutoInit(document.body);
    demo();
});


function demo() {
    const projects = [
        {
            title: 'Notepad',
            visibility: 'public',
            permissions: {
                role: 'maintainer'
            },
            web_url: './project/index.html'
        },
        {
            title: 'Wonder Project',
            visibility: 'private',
            permissions: {
                role: 'tester'
            },
            web_url: './project/index.html'
        },
        {
            title: 'Rocket Launcher',
            visibility: 'private',
            permissions: {
                role: 'test_developer'
            },
            web_url: './project/index.html'
        },
        {
            title: 'Pet Feeder',
            visibility: 'public',
            permissions: {
                role: 'tester'
            },
            web_url: './project/index.html'
        },
        {
            title: 'Just Walk',
            visibility: 'private',
            permissions: {
                role: 'test_developer'
            },
            web_url: './project/index.html'
        },
    ];

    const test_plans = [
        {
            title: 'Client ABC Release',
            current_build: {
                title: '4.3.0',
                passed: 100,
                failed: 21,
                not_run: 0,
            },
            last_update: '1 month',
        },
        {
            title: 'Continuous Integration',
            current_build: {
                title: '87a7154e2b3a02b05c3152a27a0d7f992899127c',
                passed: 139,
                failed: 0,
                not_run: 1,
            },
            last_update: '1 minute',
        },
        {
            title: 'Internal Release',
            current_build: {
                title: '4.3.12',
                passed: 100,
                failed: 21,
                not_run: 0,
            },
            last_update: '4 days',
        },
        {
            title: 'Development',
            current_build: {
                title: 'AutomatedTest #309 - 2019-03-20 10:59:32',
                passed: 1,
                failed: 0,
                not_run: 150,
            },
            last_update: 'few seconds',
        },
    ];

    for(const project of projects) {
        add_project_list_element(project, 'projects_panel');
    }

    for(const test_plan of test_plans) {
        add_test_plan_list_element(test_plan, 'test_plan_list')
    }
}