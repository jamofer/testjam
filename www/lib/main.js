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

    for(const project of projects) {
        add_project_list_element(project, 'projects_panel');
    }
}