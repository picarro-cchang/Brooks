import React, { FC } from 'react';
import _ from 'lodash';
import TopSectionItem from './TopSectionItem';
import config from '../../config';

const TopSection: FC<any> = () => {
  const navTree = _.cloneDeep(config.bootData.navTree);
  const mainLinks = _.filter(navTree, item => !item.hideFromMenu);
  const mainLinks2 = _.orderBy(mainLinks, ['text'], ['desc']);

  return (
    <div className="sidemenu__top">
      {mainLinks2.map((link, index) => {
        return <TopSectionItem link={link} key={`${link.id}-${index}`} />;
      })}
    </div>
  );
};

export default TopSection;
