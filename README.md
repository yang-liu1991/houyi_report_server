<h2 id="toc_0">此服务提供两部分功能：</h2>

<p>1、提供Amazon广告活动的同步功能，如果用户在Amazon平台创建了campaign、adgroup、product ads或keywords，模块会自动将这些信息同步到后羿系统中；</p>

<p>启动脚本：<code>sh bin/sync_server.sh start</code></p>

<p>2、提供Amazon广告投放的数据统计功能，统计级别包括campaign、adgroup、product ad、keyword，由于Amazon只提供天级别的数据统计，暂不支持小时级别数据统计；</p>

<p>启动脚本：<code>sh bin/report_server.sh start</code></p>
